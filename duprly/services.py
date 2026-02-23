from __future__ import annotations

import base64
import json
import os
import re
import subprocess
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from loguru import logger
from openpyxl import Workbook
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from duprly.compat_click import click
from duprly.runtime import AppRuntime
from duprly.ui import UI
from duprly.dupr_db import (
    Match,
    MatchDetail,
    Player,
    PlayerMatchRaw,
    PlayerMetadataSnapshot,
    PlayerRatingHistory,
    Rating,
)


def _default_date_range(days_back: int = 365 * 2) -> tuple[str, str]:
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    return start_date, end_date


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_match_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[str, Optional[str], Optional[str]]:
    if start_date is None and end_date is None:
        return "ALL", None, None

    normalized_start = start_date or "1970-01-01"
    normalized_end = end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return "RANGE", normalized_start, normalized_end


def _error_detail(runtime: AppRuntime, max_len: int = 280) -> str:
    raw = str(getattr(runtime.client, "last_error_text", "") or "").strip()
    if not raw:
        return ""
    compact = " ".join(raw.split())
    if len(compact) > max_len:
        return compact[:max_len] + "..."
    return compact


def _normalize_rating_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[str, str]:
    utc_today = datetime.now(timezone.utc).date()
    normalized_end = end_date or utc_today.strftime("%Y-%m-%d")
    if start_date:
        normalized_start = start_date
    else:
        normalized_start = (utc_today - timedelta(days=730)).strftime("%Y-%m-%d")
    return normalized_start, normalized_end


def _rating_types_from_input(rating_type: str) -> list[str]:
    normalized = (rating_type or "both").strip().lower()
    if normalized == "both":
        return ["SINGLES", "DOUBLES"]
    if normalized == "singles":
        return ["SINGLES"]
    if normalized == "doubles":
        return ["DOUBLES"]
    raise click.ClickException("Invalid rating type. Use one of: both, singles, doubles.")


def _upsert_player_snapshot(
    sess: Session,
    dupr_id: int,
    *,
    player_full_name: Optional[str] = None,
    player_metadata: Optional[dict] = None,
) -> PlayerMetadataSnapshot:
    snap = sess.execute(
        select(PlayerMetadataSnapshot).where(PlayerMetadataSnapshot.player_dupr_id == dupr_id)
    ).scalar_one_or_none()

    now = _utcnow()
    if snap is None:
        snap = PlayerMetadataSnapshot(
            player_dupr_id=dupr_id,
            player_full_name=player_full_name,
            player_metadata_json=json.dumps(player_metadata or {}, ensure_ascii=False),
            player_metadata_updated_at=now,
        )
    else:
        if player_full_name:
            snap.player_full_name = player_full_name
        if player_metadata is not None:
            snap.player_metadata_json = json.dumps(player_metadata, ensure_ascii=False)
            snap.player_metadata_updated_at = now
    sess.add(snap)
    return snap


def _update_player_snapshot_from_payload(sess: Session, pdata: dict) -> Optional[PlayerMetadataSnapshot]:
    pid = pdata.get("id")
    if pid is None:
        return None
    return _upsert_player_snapshot(
        sess,
        int(pid),
        player_full_name=pdata.get("fullName"),
        player_metadata=pdata,
    )


def _update_match_sync_snapshot(
    runtime: AppRuntime,
    dupr_id: str,
    scope: str,
    start_date: Optional[str],
    end_date: Optional[str],
    matches_count: int,
) -> bool:
    with Session(runtime.engine) as sess:
        existing = sess.execute(
            select(PlayerMetadataSnapshot).where(PlayerMetadataSnapshot.player_dupr_id == int(dupr_id))
        ).scalar_one_or_none()
        if existing is None:
            player = sess.execute(select(Player).where(Player.dupr_id == int(dupr_id))).scalar_one_or_none()
            metadata: dict[str, Any] = {}
            player_name = player.full_name if player else None
            if player:
                metadata = {
                    "id": player.dupr_id,
                    "fullName": player.full_name,
                    "gender": player.gender,
                    "age": player.age,
                }
            existing = _upsert_player_snapshot(
                sess,
                int(dupr_id),
                player_full_name=player_name,
                player_metadata=metadata,
            )

        existing.matches_updated_at = _utcnow()
        existing.matches_scope = scope
        existing.matches_start_date = start_date if scope == "RANGE" else None
        existing.matches_end_date = end_date if scope == "RANGE" else None
        existing.matches_count = matches_count
        sess.add(existing)
        sess.commit()
    return True


def _persist_raw_matches(
    runtime: AppRuntime,
    dupr_id: str,
    matches: Iterable[dict],
    scope: str,
) -> dict[str, int]:
    inserted = 0
    updated = 0
    deleted = 0
    pid = int(dupr_id)

    with Session(runtime.engine) as sess:
        if scope == "ALL":
            deleted = sess.query(PlayerMatchRaw).filter(PlayerMatchRaw.player_dupr_id == pid).delete()

        for mdata in matches:
            match_id = mdata.get("matchId") or mdata.get("id")
            if match_id is None:
                continue
            payload = json.dumps(mdata, ensure_ascii=False)
            existing = sess.execute(
                select(PlayerMatchRaw).where(
                    PlayerMatchRaw.player_dupr_id == pid,
                    PlayerMatchRaw.match_id == int(match_id),
                )
            ).scalar_one_or_none()

            if existing:
                existing.match_json = payload
                existing.fetched_at = _utcnow()
                sess.add(existing)
                updated += 1
            else:
                sess.add(
                    PlayerMatchRaw(
                        player_dupr_id=pid,
                        match_id=int(match_id),
                        match_json=payload,
                        fetched_at=_utcnow(),
                    )
                )
                inserted += 1
        sess.commit()
    return {"inserted": inserted, "updated": updated, "deleted": deleted}


def _persist_rating_history(
    runtime: AppRuntime,
    dupr_id: str,
    rating_type: str,
    start_date: str,
    end_date: str,
    rows: Iterable[dict],
) -> dict[str, int]:
    player_id = int(dupr_id)
    inserted = 0
    deleted = 0
    normalized_type = rating_type.upper()
    fetched_at = _utcnow()

    with Session(runtime.engine) as sess:
        deleted = sess.query(PlayerRatingHistory).filter(
            PlayerRatingHistory.player_dupr_id == player_id,
            PlayerRatingHistory.rating_type == normalized_type,
            PlayerRatingHistory.scope_start_date == start_date,
            PlayerRatingHistory.scope_end_date == end_date,
        ).delete()

        for idx, item in enumerate(rows):
            rating_date = item.get("date")
            if not rating_date:
                rating_date = start_date
            sess.add(
                PlayerRatingHistory(
                    player_dupr_id=player_id,
                    rating_type=normalized_type,
                    scope_start_date=start_date,
                    scope_end_date=end_date,
                    row_index=idx,
                    rating_date=str(rating_date),
                    match_date=item.get("matchDate"),
                    rating=item.get("rating"),
                    changed_by_admin=item.get("changedByAdmin"),
                    rating_history_json=json.dumps(item, ensure_ascii=False),
                    fetched_at=fetched_at,
                )
            )
            inserted += 1
        sess.commit()

    return {"inserted": inserted, "deleted": deleted}


def _coerce_rating_value(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.upper() == "NR" or text.lower() == "none":
        return None
    try:
        return float(text)
    except Exception:
        return None


def _normalize_date_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    with suppress(Exception):
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    return None


def _date_in_scope(day: Optional[str], start_date: str, end_date: str) -> bool:
    if not day:
        return False
    return start_date <= day <= end_date


def _derive_rating_points_from_raw_matches(
    runtime: AppRuntime,
    dupr_id: str,
    rating_type: str,
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]]:
    player_id = int(dupr_id)
    rating_type_upper = rating_type.upper()
    rating_key = "doubles" if rating_type_upper == "DOUBLES" else "singles"
    metric_key = "Double" if rating_type_upper == "DOUBLES" else "Single"

    with Session(runtime.engine) as sess:
        raw_rows = sess.execute(
            select(PlayerMatchRaw).where(PlayerMatchRaw.player_dupr_id == player_id)
        ).scalars().all()

    points: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    for raw in raw_rows:
        with suppress(Exception):
            match_payload = json.loads(raw.match_json)
            match_id = match_payload.get("matchId") or match_payload.get("id")
            event_date = _normalize_date_text(match_payload.get("eventDate") or match_payload.get("date"))
            if not _date_in_scope(event_date, start_date, end_date):
                continue

            for team in match_payload.get("teams") or []:
                pre_impact = team.get("preMatchRatingAndImpact") or {}
                for player_key, idx in (("player1", 1), ("player2", 2)):
                    player_data = team.get(player_key) or {}
                    pid = player_data.get("id")
                    if pid is None or int(pid) != player_id:
                        continue

                    post_rating = _coerce_rating_value((player_data.get("postMatchRating") or {}).get(rating_key))
                    pre_rating = _coerce_rating_value(pre_impact.get(f"preMatch{metric_key}RatingPlayer{idx}"))
                    impact = _coerce_rating_value(pre_impact.get(f"match{metric_key}RatingImpactPlayer{idx}"))
                    computed_rating = None
                    if pre_rating is not None and impact is not None:
                        computed_rating = pre_rating + impact

                    derived_from = "postMatchRating" if post_rating is not None else "preMatchRatingAndImpact"
                    rating_value = post_rating if post_rating is not None else computed_rating
                    if rating_value is None:
                        continue

                    dedupe_key = (event_date, int(match_id or 0), round(float(rating_value), 8), derived_from)
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)

                    points.append(
                        {
                            "date": event_date,
                            "matchDate": event_date,
                            "rating": float(rating_value),
                            "changedByAdmin": False,
                            "source": "player_match_raw",
                            "derivedFrom": derived_from,
                            "matchId": match_id,
                            "ratingType": rating_type_upper,
                            "eventName": match_payload.get("eventName") or match_payload.get("league"),
                        }
                    )

    points.sort(key=lambda row: ((row.get("date") or ""), int(row.get("matchId") or 0)))
    return points


def _derive_rating_point_from_player_snapshot(
    runtime: AppRuntime,
    dupr_id: str,
    rating_type: str,
    start_date: str,
    end_date: str,
) -> Optional[dict[str, Any]]:
    player_id = int(dupr_id)
    rating_type_upper = rating_type.upper()
    rating_key = "doubles" if rating_type_upper == "DOUBLES" else "singles"
    verified_key = f"{rating_key}Verified"
    provisional_key = f"{rating_key}Provisional"

    with Session(runtime.engine) as sess:
        snap = sess.execute(
            select(PlayerMetadataSnapshot).where(PlayerMetadataSnapshot.player_dupr_id == player_id)
        ).scalar_one_or_none()
    if snap is None:
        return None

    with suppress(Exception):
        metadata = json.loads(snap.player_metadata_json or "{}")
        rating = _coerce_rating_value(metadata.get(rating_key))
        verified_rating = _coerce_rating_value(metadata.get(verified_key))
        if rating is None:
            rating = verified_rating
        if rating is None:
            return None
        snapshot_date = snap.player_metadata_updated_at.date().isoformat()
        if not _date_in_scope(snapshot_date, start_date, end_date):
            return None
        return {
            "date": snapshot_date,
            "matchDate": None,
            "rating": float(rating),
            "changedByAdmin": None,
            "source": "player_metadata_snapshot",
            "derivedFrom": "currentPlayerMetadata",
            "playerId": player_id,
            "isProvisional": bool(metadata.get(provisional_key)),
            "verifiedRating": verified_rating,
            "ratingType": rating_type_upper,
        }
    return None


def _derive_rating_history_fallback(
    runtime: AppRuntime,
    dupr_id: str,
    rating_type: str,
    start_date: str,
    end_date: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    points = _derive_rating_points_from_raw_matches(
        runtime=runtime,
        dupr_id=dupr_id,
        rating_type=rating_type,
        start_date=start_date,
        end_date=end_date,
    )
    sources: list[str] = []
    if points:
        sources.append("player_match_raw")

    snapshot_point = _derive_rating_point_from_player_snapshot(
        runtime=runtime,
        dupr_id=dupr_id,
        rating_type=rating_type,
        start_date=start_date,
        end_date=end_date,
    )
    if snapshot_point is not None:
        snapshot_dup = any(
            p.get("date") == snapshot_point.get("date")
            and _coerce_rating_value(p.get("rating")) == _coerce_rating_value(snapshot_point.get("rating"))
            for p in points
        )
        if not snapshot_dup:
            points.append(snapshot_point)
            points.sort(key=lambda row: ((row.get("date") or ""), int(row.get("matchId") or 0)))
        sources.append("player_metadata_snapshot")

    used = len(points) > 0
    fallback_meta = {
        "used": used,
        "sources": sorted(set(sources)),
        "rows": len(points),
    }
    if not used:
        fallback_meta["reason"] = "No match-derived or metadata-derived rating points available."
    return points, fallback_meta


def ensure_auth(runtime: AppRuntime, ui: UI) -> None:
    runtime.load_environment()
    username = os.getenv("DUPR_USERNAME")
    password = os.getenv("DUPR_PASSWORD")
    access_token = os.getenv("DUPR_ACCESS_TOKEN")
    if not access_token and (not username or not password):
        raise click.ClickException(
            "Missing DUPR credentials. Set DUPR_USERNAME and DUPR_PASSWORD, "
            "or provide DUPR_ACCESS_TOKEN."
        )

    with ui.status("Authenticating with DUPR"):
        rc = runtime.client.auth_user(username or "", password or "")
    if rc not in (0, 200):
        raise click.ClickException(f"Authentication failed (HTTP {rc}).")


def _redact_secret(value: str, prefix: int = 12, suffix: int = 8) -> str:
    if len(value) <= (prefix + suffix + 3):
        return value[:prefix] + "..."
    return f"{value[:prefix]}...{value[-suffix:]}"


def _startup_token_preview(token: str) -> str:
    t = token.strip()
    if not t:
        return "missing"
    if len(t) <= 6:
        return _redact_secret(t, prefix=1, suffix=1)
    return f"{t[:2]}**...***{t[-3:]}"


def _decode_jwt_expiry(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        padded = payload_b64 + "=" * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
        exp = payload.get("exp")
        if not exp:
            return None
        return datetime.fromtimestamp(int(exp), tz=timezone.utc).isoformat()
    except Exception:
        return None


def _parse_cookie_string(cookie_string: str, cookie_name: str) -> str | None:
    for part in cookie_string.split(";"):
        name, sep, value = part.strip().partition("=")
        if sep != "=":
            continue
        if name == cookie_name and value:
            return value
    return None


def _dashboard_host_for_domain(domain: str) -> str:
    normalized = domain.strip().lower().lstrip(".")
    if not normalized:
        return "dashboard.dupr.com"
    if normalized.startswith("dashboard."):
        return normalized
    if "." not in normalized:
        return normalized
    return f"dashboard.{normalized}"


def _chromium_applescript_app_name(browser: str) -> str | None:
    mapping = {
        "chrome": "Google Chrome",
        "chromium": "Chromium",
        "brave": "Brave Browser",
        "edge": "Microsoft Edge",
        "comet": "Comet",
    }
    return mapping.get(browser)


def _extract_dupr_token_from_chromium_javascript(browser: str, domain: str, cookie_name: str) -> str | None:
    """
    Fallback path for Chromium-family browsers when cookie DB decryption fails.
    Requires browser scripting permission in macOS Automation settings.
    """
    app_name = _chromium_applescript_app_name(browser)
    if not app_name:
        return None

    dashboard_host = _dashboard_host_for_domain(domain)
    domain_hint = domain.strip().lower().lstrip(".")
    script = f"""
set targetCookie to "{cookie_name}="
set domainHint to "{domain_hint}"
set openUrl to "https://{dashboard_host}/"
set cookieString to ""
set openedTab to false
set targetTab to missing value
tell application "{app_name}"
  if not running then
    activate
    delay 1.2
  end if
  if (count of windows) = 0 then
    make new window
  end if
  repeat with w in windows
    repeat with t in tabs of w
      try
        set tabUrl to URL of t
      on error
        set tabUrl to ""
      end try
      if tabUrl contains domainHint then
        set targetTab to t
        exit repeat
      end if
    end repeat
    if targetTab is not missing value then exit repeat
  end repeat
  if targetTab is missing value then
    tell front window
      set targetTab to make new tab with properties {{URL:openUrl}}
    end tell
    set openedTab to true
    delay 1.2
  end if
  try
    set cookieString to execute targetTab javascript "document.cookie"
  on error
    set cookieString to ""
  end try
  if openedTab and targetTab is not missing value then
    try
      close targetTab
    end try
  end if
end tell
return cookieString
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None
    cookie_string = (result.stdout or "").strip()
    if not cookie_string:
        return None
    return _parse_cookie_string(cookie_string, cookie_name)


def extract_dupr_token_from_browser(
    runtime: AppRuntime,
    ui: UI,
    browser: str = "safari",
    domain: str = "dupr.com",
    cookie_name: str = "dupr_access_token",
    save: bool = True,
) -> dict[str, Any]:
    runtime.load_environment()
    loader_error: Exception | None = None
    cookie_jar = []
    bc3_error: Exception | None = None
    with ui.status(f"Reading {browser} cookies for {domain}"):
        try:
            import browser_cookie3 as bc3  # type: ignore
        except Exception as err:
            bc3 = None
            bc3_error = err

        loaders = {
            "safari": getattr(bc3, "safari", None) if bc3 else None,
            "chrome": getattr(bc3, "chrome", None) if bc3 else None,
            "chromium": getattr(bc3, "chromium", None) if bc3 else None,
            "brave": getattr(bc3, "brave", None) if bc3 else None,
            "edge": getattr(bc3, "edge", None) if bc3 else None,
            "firefox": getattr(bc3, "firefox", None) if bc3 else None,
            "comet": getattr(bc3, "chromium", None) if bc3 else None,
        }
        loader = loaders.get(browser)
        if loader is None and browser != "comet":
            if bc3_error and browser in ("safari", "chrome", "chromium", "brave", "edge", "firefox"):
                raise click.ClickException(
                    "browser-cookie3 is required for browser token extraction. "
                    "Install dependencies with `pip install -r requirements.txt`."
                ) from bc3_error
            raise click.ClickException(f"Unsupported browser '{browser}'.")

        if loader:
            try:
                if browser == "comet":
                    cookie_file = Path.home() / "Library/Application Support/Comet/Default/Cookies"
                    key_file = Path.home() / "Library/Application Support/Comet/Local State"
                    cookie_jar = loader(
                        cookie_file=str(cookie_file),
                        key_file=str(key_file),
                        domain_name=domain,
                    )
                else:
                    cookie_jar = loader(domain_name=domain)
            except TypeError:
                try:
                    cookie_jar = loader()
                except Exception as err:
                    loader_error = err
                    cookie_jar = []
            except Exception as err:
                loader_error = err
                cookie_jar = []

    access_token: str | None = None
    refresh_token: str | None = None
    domain_lower = domain.lower()
    for cookie in cookie_jar:
        cookie_domain = (cookie.domain or "").lower().lstrip(".")
        if domain_lower not in cookie_domain:
            continue
        if cookie.name == cookie_name and cookie.value:
            access_token = cookie.value
        if cookie.name == "dupr_refresh_token" and cookie.value:
            refresh_token = cookie.value

    if not access_token:
        if browser == "safari":
            access_token = _extract_dupr_token_from_safari_javascript(domain=domain, cookie_name=cookie_name)
            if access_token:
                if save:
                    runtime.client.access_token = access_token
                    runtime.client.save_token()
                    os.environ["DUPR_ACCESS_TOKEN"] = access_token
                return {
                    "browser": "safari-js",
                    "domain": domain,
                    "cookie_name": cookie_name,
                    "token_found": True,
                    "refresh_token_found": bool(refresh_token),
                    "saved": save,
                    "config_path": runtime.client.env_path,
                    "token_preview": _redact_secret(access_token),
                    "token_expires_at_utc": _decode_jwt_expiry(access_token),
                    "token": access_token,
                }
        elif browser in ("chrome", "chromium", "brave", "edge", "comet"):
            access_token = _extract_dupr_token_from_chromium_javascript(
                browser=browser,
                domain=domain,
                cookie_name=cookie_name,
            )
            if access_token:
                if save:
                    runtime.client.access_token = access_token
                    runtime.client.save_token()
                    os.environ["DUPR_ACCESS_TOKEN"] = access_token
                return {
                    "browser": f"{browser}-js",
                    "domain": domain,
                    "cookie_name": cookie_name,
                    "token_found": True,
                    "refresh_token_found": bool(refresh_token),
                    "saved": save,
                    "config_path": runtime.client.env_path,
                    "token_preview": _redact_secret(access_token),
                    "token_expires_at_utc": _decode_jwt_expiry(access_token),
                    "token": access_token,
                }

        # Try to locate the same cookie across all domains to provide a precise hint.
        candidate_domains: list[str] = []
        if loader:
            try:
                full_cookie_jar = loader()
                for cookie in full_cookie_jar:
                    if cookie.name != cookie_name or not cookie.value:
                        continue
                    cdom = (cookie.domain or "").lstrip(".")
                    if cdom:
                        candidate_domains.append(cdom)
            except Exception:
                pass

        if candidate_domains:
            unique_domains = sorted(set(candidate_domains))
            suggested_domain = unique_domains[0]
            raise click.ClickException(
                f"Could not find cookie '{cookie_name}' for domain '{domain}' in {browser}. "
                f"Found '{cookie_name}' in domain(s): {', '.join(unique_domains)}. "
                f"Try `--domain {suggested_domain}` or pass token directly with `--token`."
            )
        if loader_error:
            raise click.ClickException(
                f"Could not extract cookie '{cookie_name}' from {browser}: {loader_error}. "
                "A browser JavaScript fallback was also attempted but did not return the token. "
                "Make sure you are logged in on dashboard.dupr.com and allow Automation access, "
                "or pass token directly with `--token`."
            )
        raise click.ClickException(
            f"Could not find cookie '{cookie_name}' for domain '{domain}' in {browser}. "
            f"You can pass token directly with `--token`."
        )

    if save:
        runtime.client.access_token = access_token
        runtime.client.save_token()
        os.environ["DUPR_ACCESS_TOKEN"] = access_token

    return {
        "browser": browser,
        "domain": domain,
        "cookie_name": cookie_name,
        "token_found": True,
        "refresh_token_found": bool(refresh_token),
        "saved": save,
        "config_path": runtime.client.env_path,
        "token_preview": _redact_secret(access_token),
        "token_expires_at_utc": _decode_jwt_expiry(access_token),
        "token": access_token,
    }


def _extract_dupr_token_from_safari_javascript(domain: str, cookie_name: str) -> str | None:
    """
    Fallback path for Safari when cookie storage lookup misses.
    Requires Safari "Allow JavaScript from Apple Events" enabled.
    """
    script = f"""
set targetCookie to "{cookie_name}="
set domainHint to "{domain.strip().lower().lstrip('.')}"
set openUrl to "https://{_dashboard_host_for_domain(domain)}/"
set cookieString to ""
set openedTab to false
set targetTab to missing value
tell application "Safari"
  if not running then
    activate
    delay 1.2
  end if
  if (count of windows) = 0 then
    make new document
  end if
  repeat with w in windows
    repeat with t in tabs of w
      try
        set tabUrl to URL of t
      on error
        set tabUrl to ""
      end try
      if tabUrl contains domainHint then
        set targetTab to t
        exit repeat
      end if
    end repeat
    if targetTab is not missing value then exit repeat
  end repeat
  if targetTab is missing value then
    tell front window
      set targetTab to make new tab with properties {{URL:openUrl}}
      set current tab to targetTab
    end tell
    set openedTab to true
    delay 1.2
  end if
  try
    set cookieString to do JavaScript "document.cookie" in targetTab
  on error
    set cookieString to ""
  end try
  if openedTab and targetTab is not missing value then
    try
      close targetTab
    end try
  end if
end tell
return cookieString
"""

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None
    cookie_string = (result.stdout or "").strip()
    if not cookie_string:
        return None

    return _parse_cookie_string(cookie_string, cookie_name)


def set_access_token(runtime: AppRuntime, token: str, save: bool = True) -> dict[str, Any]:
    runtime.load_environment()
    if not token or not token.strip():
        raise click.ClickException("Token is empty.")
    access_token = token.strip()
    if save:
        runtime.client.access_token = access_token
        runtime.client.save_token()
        os.environ["DUPR_ACCESS_TOKEN"] = access_token

    return {
        "token_found": True,
        "saved": save,
        "config_path": runtime.client.env_path,
        "token_preview": _redact_secret(access_token),
        "token_expires_at_utc": _decode_jwt_expiry(access_token),
        "token": access_token,
    }


def _save_player(sess: Session, pdata: dict) -> bool:
    player = Player().from_json(pdata)
    existing = Player.get(sess, player.dupr_id)
    Player.save(sess, player)
    return existing is None


def sync_players(runtime: AppRuntime, ui: UI, club_id: str) -> dict[str, Any]:
    ensure_auth(runtime, ui)

    with ui.status(f"Fetching players for club {club_id}"):
        rc, players = runtime.client.get_members_by_club(club_id)
    if rc != 200:
        raise click.ClickException(f"Failed to fetch players (HTTP {rc}).")

    inserted = 0
    updated = 0
    with Session(runtime.engine) as sess:
        for pdata in ui.track(players, "Saving players"):
            if _save_player(sess, pdata):
                inserted += 1
            else:
                updated += 1
        sess.commit()

    return {
        "club_id": club_id,
        "total": len(players),
        "inserted": inserted,
        "updated": updated,
    }


def fetch_player(runtime: AppRuntime, ui: UI, pid: str, persist: bool = True) -> dict:
    ensure_auth(runtime, ui)
    with ui.status(f"Fetching player {pid}"):
        rc, pdata = runtime.client.get_player(pid)

    if rc != 200 or not pdata:
        raise click.ClickException(f"Failed to fetch player {pid} (HTTP {rc}).")

    if persist:
        with Session(runtime.engine) as sess:
            _save_player(sess, pdata)
            _update_player_snapshot_from_payload(sess, pdata)
            sess.commit()

    return pdata


def _persist_matches(runtime: AppRuntime, ui: UI, matches: Iterable[dict]) -> dict[str, int]:
    inserted = 0
    skipped = 0

    with Session(runtime.engine) as sess:
        for mdata in matches:
            match = Match().from_json(mdata)
            existing = Match.get_by_id(sess, match.match_id)
            if existing:
                skipped += 1
                continue

            for team in match.teams:
                resolved_players = []
                for player in team.players:
                    p1 = sess.execute(select(Player).where(Player.dupr_id == player.dupr_id)).scalar_one_or_none()
                    if p1:
                        resolved_players.append(p1)
                        continue

                    # Handle duplicate player entries in a doubles team.
                    duplicate = any(p.dupr_id == player.dupr_id for p in resolved_players)
                    if duplicate:
                        logger.warning(
                            "same player on doubles team {} for match {}", player.dupr_id, match.match_id
                        )
                        continue
                    resolved_players.append(player)
                team.players = resolved_players

            sess.add(match)
            inserted += 1

        sess.commit()

    return {"inserted": inserted, "skipped": skipped}


def fetch_matches(
    runtime: AppRuntime,
    ui: UI,
    dupr_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    ensure_auth(runtime, ui)
    scope, normalized_start_date, normalized_end_date = _normalize_match_range(start_date, end_date)

    with ui.status(f"Fetching matches for player {dupr_id}"):
        if scope == "ALL":
            rc, matches = runtime.client.get_member_match_history_all(dupr_id)
        else:
            rc, matches = runtime.client.get_member_match_history_range(
                dupr_id,
                start_date=normalized_start_date or "1970-01-01",
                end_date=normalized_end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )

    if rc != 200:
        detail = _error_detail(runtime)
        if detail:
            raise click.ClickException(f"Failed to fetch matches for {dupr_id} (HTTP {rc}): {detail}")
        raise click.ClickException(f"Failed to fetch matches for {dupr_id} (HTTP {rc}).")

    persisted = {"inserted": 0, "skipped": 0}
    raw_persisted = {"inserted": 0, "updated": 0, "deleted": 0}
    snapshot_updated = False
    if persist:
        persisted = _persist_matches(runtime, ui, matches)
        raw_persisted = _persist_raw_matches(runtime, dupr_id=dupr_id, matches=matches, scope=scope)
        snapshot_updated = _update_match_sync_snapshot(
            runtime,
            dupr_id=dupr_id,
            scope=scope,
            start_date=normalized_start_date,
            end_date=normalized_end_date,
            matches_count=len(matches),
        )

    return {
        "dupr_id": dupr_id,
        "scope": scope,
        "start_date": normalized_start_date,
        "end_date": normalized_end_date,
        "match_count": len(matches),
        "persisted": persisted,
        "raw_persisted": raw_persisted,
        "snapshot_updated": snapshot_updated,
        "matches": matches,
    }


def fetch_rating_history(
    runtime: AppRuntime,
    ui: UI,
    dupr_id: str,
    rating_type: str = "both",
    start_date: str | None = None,
    end_date: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    ensure_auth(runtime, ui)
    normalized_start, normalized_end = _normalize_rating_range(start_date, end_date)
    rating_types = _rating_types_from_input(rating_type)

    histories: dict[str, list[dict]] = {}
    counts: dict[str, int] = {}
    persisted_by_type: dict[str, dict[str, int]] = {}
    fallback_by_type: dict[str, dict[str, Any]] = {}

    for rtype in rating_types:
        with ui.status(f"Fetching {rtype.lower()} rating history for player {dupr_id}"):
            rc, rows = runtime.client.get_player_rating_history(
                member_id=dupr_id,
                rating_type=rtype,
                start_date=normalized_start,
                end_date=normalized_end,
            )
        if rc != 200:
            raise click.ClickException(
                f"Failed to fetch {rtype.lower()} rating history for {dupr_id} (HTTP {rc})."
            )
        fallback_meta: dict[str, Any] = {"used": False, "sources": [], "rows": len(rows)}
        if not rows:
            rows, fallback_meta = _derive_rating_history_fallback(
                runtime=runtime,
                dupr_id=dupr_id,
                rating_type=rtype,
                start_date=normalized_start,
                end_date=normalized_end,
            )
        histories[rtype.lower()] = rows
        counts[rtype.lower()] = len(rows)
        fallback_by_type[rtype.lower()] = fallback_meta
        if persist:
            persisted_by_type[rtype.lower()] = _persist_rating_history(
                runtime=runtime,
                dupr_id=dupr_id,
                rating_type=rtype,
                start_date=normalized_start,
                end_date=normalized_end,
                rows=rows,
            )
        else:
            persisted_by_type[rtype.lower()] = {"inserted": 0, "deleted": 0}

    return {
        "dupr_id": dupr_id,
        "type_requested": rating_type,
        "types_fetched": [t.lower() for t in rating_types],
        "start_date": normalized_start,
        "end_date": normalized_end,
        "histories": histories,
        "counts": counts,
        "fallback": fallback_by_type,
        "persisted": persisted_by_type,
    }


def _db_player_ids(runtime: AppRuntime) -> list[str]:
    with Session(runtime.engine) as sess:
        rows = sess.execute(select(Player.dupr_id)).all()
        return [str(row[0]) for row in rows if row and row[0] is not None]


def sync_matches(
    runtime: AppRuntime,
    ui: UI,
    dupr_id: str | None,
    all_players: bool,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, Any]:
    ensure_auth(runtime, ui)

    if all_players:
        player_ids = _db_player_ids(runtime)
        if not player_ids:
            raise click.ClickException(
                "No players found in the local database. Run 'duprly sync players' first."
            )
    elif dupr_id:
        player_ids = [str(dupr_id)]
    else:
        raise click.ClickException("Provide --dupr-id or use --all-players.")

    if not start_date or not end_date:
        start_date, end_date = _default_date_range()

    total_matches = 0
    inserted = 0
    skipped = 0
    failures: list[dict[str, Any]] = []

    for pid in ui.track(player_ids, "Fetching match history"):
        rc, matches = runtime.client.get_member_match_history_p(pid, start_date, end_date)
        if rc != 200:
            failures.append({"dupr_id": pid, "status": rc})
            continue

        total_matches += len(matches)
        persisted = _persist_matches(runtime, ui, matches)
        inserted += persisted["inserted"]
        skipped += persisted["skipped"]

    return {
        "players_processed": len(player_ids),
        "total_matches": total_matches,
        "inserted": inserted,
        "skipped": skipped,
        "failures": failures,
        "start_date": start_date,
        "end_date": end_date,
    }


def sync_ratings(runtime: AppRuntime, ui: UI, all_players: bool) -> dict[str, Any]:
    ensure_auth(runtime, ui)

    with Session(runtime.engine) as sess:
        if all_players:
            ids = [str(v) for v in sess.scalars(select(Player.dupr_id)).all() if v is not None]
        else:
            q = (
                select(Player.dupr_id)
                .join(Player.rating, isouter=True)
                .where(or_(Rating.id.is_(None), Rating.singles.is_(None), Rating.doubles.is_(None)))
            )
            ids = [str(v) for v in sess.scalars(q).all() if v is not None]

    updated = 0
    failed: list[dict[str, Any]] = []
    for pid in ui.track(ids, "Refreshing ratings"):
        rc, pdata = runtime.client.get_player(pid)
        if rc != 200 or not pdata:
            failed.append({"dupr_id": pid, "status": rc})
            continue
        with Session(runtime.engine) as sess:
            _save_player(sess, pdata)
            sess.commit()
        updated += 1

    return {
        "requested": len(ids),
        "updated": updated,
        "failed": failed,
        "mode": "all" if all_players else "missing-only",
    }


def sync_all(runtime: AppRuntime, ui: UI, club_id: str, start_date: str | None, end_date: str | None) -> dict[str, Any]:
    players_result = sync_players(runtime, ui, club_id)
    matches_result = sync_matches(
        runtime,
        ui,
        dupr_id=None,
        all_players=True,
        start_date=start_date,
        end_date=end_date,
    )
    ratings_result = sync_ratings(runtime, ui, all_players=False)

    return {
        "players": players_result,
        "matches": matches_result,
        "ratings": ratings_result,
    }


def search_clubs(runtime: AppRuntime, ui: UI, query: str, limit: int = 10) -> list[dict]:
    ensure_auth(runtime, ui)
    with ui.status(f"Searching clubs for '{query}'"):
        rc, clubs = runtime.client.search_clubs(query, limit=limit)
    if rc != 200:
        raise click.ClickException(f"Club search failed (HTTP {rc}).")
    return clubs


def search_players(runtime: AppRuntime, ui: UI, query: str, limit: int = 8) -> list[dict]:
    ensure_auth(runtime, ui)
    with ui.status(f"Searching players for '{query}'"):
        rc, players = runtime.client.search_players(query=query, limit=limit)
    if rc != 200:
        raise click.ClickException(f"Player search failed (HTTP {rc}).")
    return players


def resolve_lookup_selection(
    runtime: AppRuntime,
    ui: UI,
    entity: str,
    selection: dict,
    persist: bool = True,
) -> dict[str, Any]:
    if entity == "player":
        player_id = selection.get("id") or selection.get("duprId")
        if player_id is None:
            raise click.ClickException("Unable to resolve player ID from selection.")
        pdata = fetch_player(runtime, ui, str(player_id), persist=persist)
        return {
            "entity": "player",
            "selection": selection,
            "player": pdata,
        }
    if entity == "club":
        return {
            "entity": "club",
            "selection": selection,
            "club": {
                "clubId": selection.get("clubId"),
                "clubName": selection.get("clubName"),
                "shortAddress": selection.get("shortAddress", ""),
            },
        }
    raise click.ClickException(f"Unsupported lookup entity '{entity}'.")


def export_club_players(
    runtime: AppRuntime,
    ui: UI,
    club_query: str | None,
    club_id: str | None,
    output_path: str | None,
    non_interactive: bool,
) -> dict[str, Any]:
    ensure_auth(runtime, ui)

    selected_club: dict[str, Any] | None = None
    if club_id:
        selected_club = {"clubId": club_id, "clubName": f"club_{club_id}"}
    else:
        if not club_query:
            raise click.ClickException("Provide CLUB_QUERY or --club-id.")
        clubs = search_clubs(runtime, ui, club_query, limit=20)
        if not clubs:
            raise click.ClickException(f"No clubs found for query '{club_query}'.")

        if len(clubs) == 1 or non_interactive:
            selected_club = clubs[0]
        else:
            rows = []
            for idx, club in enumerate(clubs, start=1):
                rows.append(
                    (
                        idx,
                        club.get("clubName", "Unknown"),
                        club.get("clubId", "Unknown"),
                        club.get("shortAddress", ""),
                    )
                )
            ui.table("Club Matches", ["#", "Name", "ID", "Location"], rows)
            choice = ui.ask_int("Select club number")
            if choice < 1 or choice > len(clubs):
                raise click.ClickException("Selection out of range.")
            selected_club = clubs[choice - 1]

    club_id_str = str(selected_club.get("clubId"))
    with ui.status(f"Fetching players for club {club_id_str}"):
        rc, players = runtime.client.get_members_by_club(club_id_str)
    if rc != 200:
        raise click.ClickException(f"Failed to fetch players (HTTP {rc}).")

    club_name = selected_club.get("clubName", f"club_{club_id_str}")
    if not output_path:
        stamp = datetime.now().strftime("%Y-%m-%d")
        safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", club_name).strip("_").lower() or "club"
        output_path = f"club_players_{club_id_str}_{safe_name}_{stamp}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)

    return {
        "club_id": club_id_str,
        "club_name": club_name,
        "players": len(players),
        "output": output_path,
    }


def export_rankings(runtime: AppRuntime, ui: UI, club_id: str, output_path: str | None) -> dict[str, Any]:
    ensure_auth(runtime, ui)
    with ui.status(f"Fetching rankings for club {club_id}"):
        rc, rankings = runtime.client.get_members_by_club_ranking(club_id, get_all=True)
    if rc != 200:
        raise click.ClickException(f"Failed to fetch rankings (HTTP {rc}).")

    if not output_path:
        output_path = f"rankings-{club_id}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rankings, f, indent=2, ensure_ascii=False)

    return {
        "club_id": club_id,
        "players": len(rankings),
        "output": output_path,
    }


def export_workbook(runtime: AppRuntime, ui: UI, output_path: str) -> dict[str, Any]:
    wb = Workbook()
    players_sheet = wb.active
    players_sheet.title = "players"
    players_sheet.append(
        [
            "id",
            "dupr_id",
            "full_name",
            "gender",
            "age",
            "doubles",
            "doubles_verified",
            "singles",
            "singles_verified",
            "club_id",
        ]
    )

    with Session(runtime.engine) as sess:
        players = sess.scalars(select(Player)).all()
        matches = sess.scalars(select(Match)).all()

        for player in ui.track(players, "Writing player sheet"):
            rating = player.rating
            players_sheet.append(
                [
                    player.id,
                    player.dupr_id,
                    player.full_name,
                    player.gender,
                    player.age,
                    rating.doubles if rating else None,
                    rating.doubles_verified if rating else None,
                    rating.singles if rating else None,
                    rating.singles_verified if rating else None,
                    player.club_id,
                ]
            )

        matches_sheet = wb.create_sheet("matches")
        matches_sheet.append(
            [
                "match_id",
                "name",
                "date",
                "event_format",
                "source",
                "team_1",
                "team_1_score",
                "team_2",
                "team_2_score",
            ]
        )

        for match in ui.track(matches, "Writing match sheet"):
            team_1 = match.teams[0] if len(match.teams) > 0 else None
            team_2 = match.teams[1] if len(match.teams) > 1 else None
            team_1_names = ", ".join([p.full_name for p in team_1.players]) if team_1 else ""
            team_2_names = ", ".join([p.full_name for p in team_2.players]) if team_2 else ""
            matches_sheet.append(
                [
                    match.match_id,
                    match.name,
                    str(match.date),
                    getattr(match, "event_format", None),
                    match.match_source,
                    team_1_names,
                    team_1.score1 if team_1 else None,
                    team_2_names,
                    team_2.score1 if team_2 else None,
                ]
            )

    wb.save(output_path)
    return {
        "players": len(players),
        "matches": len(matches),
        "output": output_path,
    }


def db_stats(runtime: AppRuntime) -> dict[str, int]:
    with Session(runtime.engine) as sess:
        return {
            "players": sess.query(Player).count(),
            "matches": sess.query(Match).count(),
            "ratings": sess.query(Rating).count(),
            "match_detail": sess.query(MatchDetail).count(),
        }


def rebuild_match_detail(runtime: AppRuntime, ui: UI) -> dict[str, int]:
    created = 0
    skipped = 0
    with Session(runtime.engine) as sess:
        sess.execute(delete(MatchDetail))
        matches = sess.scalars(select(Match)).all()

        for match in ui.track(matches, "Building match_detail rows"):
            if len(match.teams) < 2:
                skipped += 1
                continue

            t1 = match.teams[0]
            t2 = match.teams[1]
            if not t1.players or not t2.players:
                skipped += 1
                continue

            md = MatchDetail()
            md.match = match
            md.team_1_score = t1.score1
            md.team_2_score = t2.score1
            md.team_1_player_1_id = t1.players[0].id
            md.team_1_player_2_id = t1.players[1].id if len(t1.players) > 1 else None
            md.team_2_player_1_id = t2.players[0].id
            md.team_2_player_2_id = t2.players[1].id if len(t2.players) > 1 else None
            sess.add(md)
            created += 1

        sess.commit()

    return {"created": created, "skipped": skipped}


def doctor(runtime: AppRuntime, ui: UI, check_api: bool) -> dict[str, Any]:
    runtime.load_environment()

    checks = {
        "DUPR_USERNAME": bool(os.getenv("DUPR_USERNAME")),
        "DUPR_PASSWORD": bool(os.getenv("DUPR_PASSWORD")),
        "DUPR_CLUB_ID": bool(os.getenv("DUPR_CLUB_ID")),
        "DB_EXISTS": runtime.db_path.exists(),
    }

    api_status: dict[str, Any] = {"enabled": check_api, "ok": None, "status": None}
    if check_api:
        with suppress(Exception):
            ensure_auth(runtime, ui)
            rc, profile = runtime.client.get_profile()
            api_status["status"] = rc
            api_status["ok"] = rc == 200 and profile is not None

    return {"checks": checks, "api": api_status}


def export_profile_matches(
    runtime: AppRuntime,
    ui: UI,
    start_date: str | None,
    end_date: str | None,
    output_path: str,
) -> dict[str, Any]:
    ensure_auth(runtime, ui)

    with ui.status("Fetching DUPR profile"):
        rc, profile = runtime.client.get_profile()
    if rc != 200 or not profile:
        raise click.ClickException(f"Failed to fetch profile (HTTP {rc}).")

    dupr_id = str(profile.get("id"))
    result = fetch_matches(runtime, ui, dupr_id=dupr_id, start_date=start_date, end_date=end_date, persist=False)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result["matches"], f, indent=2, ensure_ascii=False)

    return {
        "dupr_id": dupr_id,
        "matches": result["match_count"],
        "output": output_path,
        "start_date": result["start_date"],
        "end_date": result["end_date"],
    }


def interactive_quick_status(runtime: AppRuntime) -> list[tuple[str, str]]:
    runtime.load_environment()
    access_token = os.getenv("DUPR_ACCESS_TOKEN")
    if not access_token:
        with suppress(Exception):
            access_token = runtime.client.access_token

    checks = [
        ("DUPR_USERNAME", "ok" if os.getenv("DUPR_USERNAME") else "missing"),
        ("DUPR_PASSWORD", "ok" if os.getenv("DUPR_PASSWORD") else "missing"),
        ("DUPR_ACCESS_TOKEN", _startup_token_preview(access_token) if access_token else "missing"),
        ("DUPR_CLUB_ID", os.getenv("DUPR_CLUB_ID") or "missing"),
        ("dupr.sqlite", "present" if Path("dupr.sqlite").exists() else "missing"),
    ]

    with suppress(Exception):
        stats = db_stats(runtime)
        checks.append(("db players", str(stats["players"])))
        checks.append(("db matches", str(stats["matches"])))

    return checks
