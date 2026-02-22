from __future__ import annotations

import csv
import io
import json
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from duprly.clipboard import copy_text
from duprly.runtime import AppRuntime
from duprly.dupr_db import Match, Player, PlayerMatchRaw, PlayerMetadataSnapshot, PlayerRatingHistory, Rating


_SPARK_CHARS = ".:-=+*#%@"


def _rating_display(value: Any) -> str:
    if value is None:
        return "NR"
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return "NR"
        return stripped
    if isinstance(value, (int, float)):
        return f"{float(value):.3f}".rstrip("0").rstrip(".")
    return str(value)


def sparkline(values: list[float | int | None]) -> str:
    numeric = [float(v) for v in values if isinstance(v, (int, float))]
    if not numeric:
        return "(no data)"
    low = min(numeric)
    high = max(numeric)
    if low == high:
        return _SPARK_CHARS[0] * len(numeric)

    chars: list[str] = []
    bins = len(_SPARK_CHARS) - 1
    for value in numeric:
        idx = int(round(((value - low) / (high - low)) * bins))
        idx = max(0, min(bins, idx))
        chars.append(_SPARK_CHARS[idx])
    return "".join(chars)


def _safe_json_load(text: str | None) -> Any:
    if not text:
        return None
    with suppress(Exception):
        return json.loads(text)
    return None


def _to_date_str(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        with suppress(Exception):
            return value.isoformat()
    return str(value)


def _in_date_range(value: str, start_date: str | None, end_date: str | None) -> bool:
    if not value:
        return False
    if start_date and value < start_date:
        return False
    if end_date and value > end_date:
        return False
    return True


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _flatten_row_for_csv(row: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (dict, list)):
            flat[key] = json.dumps(value, ensure_ascii=False)
        else:
            flat[key] = value
    return flat


def _csv_text(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    flattened = [_flatten_row_for_csv(row) for row in rows]
    fieldnames: list[str] = []
    for row in flattened:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in flattened:
        writer.writerow(row)
    return output.getvalue()


def serialize_export(data: Any, export_format: str) -> str:
    fmt = export_format.lower()
    if fmt == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)

    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        rows = data["rows"]
    elif isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = [data]
    else:
        rows = [{"value": str(data)}]
    return _csv_text(rows)


def export_data(
    data: Any,
    export_format: str,
    output: str | None,
    clipboard: bool,
    default_prefix: str,
) -> dict[str, Any]:
    fmt = export_format.lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("export_format must be csv or json")

    text = serialize_export(data, fmt)
    target_path = output
    if not target_path and not clipboard:
        target_path = f"{default_prefix}_{_now_stamp()}.{fmt}"

    file_written = False
    if target_path:
        path = Path(target_path)
        if path.parent and str(path.parent) != ".":
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        file_written = True

    clipboard_ok = False
    clipboard_mechanism = "none"
    clipboard_reason = ""
    if clipboard:
        clipboard_ok, clipboard_mechanism, clipboard_reason = copy_text(text)
        if not clipboard_ok and not file_written:
            fallback = Path(f"{default_prefix}_{_now_stamp()}.{fmt}")
            fallback.write_text(text, encoding="utf-8")
            target_path = str(fallback)
            file_written = True

    return {
        "format": fmt,
        "output": target_path,
        "file_written": file_written,
        "clipboard": clipboard,
        "clipboard_ok": clipboard_ok,
        "clipboard_mechanism": clipboard_mechanism,
        "clipboard_reason": clipboard_reason,
        "bytes": len(text.encode("utf-8")),
    }


def list_players(runtime: AppRuntime, query: str | None, limit: int, offset: int) -> dict[str, Any]:
    with Session(runtime.engine) as sess:
        stmt = (
            select(Player, Rating, PlayerMetadataSnapshot)
            .join(Rating, Rating.player_id == Player.id, isouter=True)
            .join(
                PlayerMetadataSnapshot,
                PlayerMetadataSnapshot.player_dupr_id == Player.dupr_id,
                isouter=True,
            )
            .order_by(Player.full_name.asc())
        )

        count_stmt = select(Player)

        if query:
            q = query.strip().lower()
            if q.isdigit():
                stmt = stmt.where(Player.dupr_id == int(q))
                count_stmt = count_stmt.where(Player.dupr_id == int(q))
            else:
                pattern = f"%{q}%"
                stmt = stmt.where(Player.full_name.ilike(pattern))
                count_stmt = count_stmt.where(Player.full_name.ilike(pattern))

        total = sess.execute(count_stmt).scalars().all()
        rows = sess.execute(stmt.offset(offset).limit(limit)).all()

    items: list[dict[str, Any]] = []
    for player, rating, snapshot in rows:
        items.append(
            {
                "name": player.full_name,
                "dupr_id": player.dupr_id,
                "gender": player.gender,
                "age": player.age,
                "email": player.email,
                "phone": player.phone,
                "singles": _rating_display(getattr(rating, "singles", None)),
                "doubles": _rating_display(getattr(rating, "doubles", None)),
                "metadata_updated_at": _to_date_str(getattr(snapshot, "player_metadata_updated_at", None)),
                "matches_updated_at": _to_date_str(getattr(snapshot, "matches_updated_at", None)),
            }
        )

    return {
        "rows": items,
        "total": len(total),
        "limit": limit,
        "offset": offset,
        "query": query,
    }


def get_player_overview(runtime: AppRuntime, dupr_id: int) -> dict[str, Any] | None:
    with Session(runtime.engine) as sess:
        player = sess.execute(select(Player).where(Player.dupr_id == dupr_id)).scalar_one_or_none()
        if player is None:
            return None

        rating = player.rating
        snapshot = sess.execute(
            select(PlayerMetadataSnapshot).where(PlayerMetadataSnapshot.player_dupr_id == dupr_id)
        ).scalar_one_or_none()

    snapshot_json = _safe_json_load(getattr(snapshot, "player_metadata_json", None))
    return {
        "dupr_id": player.dupr_id,
        "name": player.full_name,
        "gender": player.gender,
        "age": player.age,
        "email": player.email,
        "phone": player.phone,
        "club_id": player.club_id,
        "ratings": {
            "singles": _rating_display(getattr(rating, "singles", None)),
            "singles_verified": _rating_display(getattr(rating, "singles_verified", None)),
            "singles_provisional": getattr(rating, "is_singles_provisional", None),
            "doubles": _rating_display(getattr(rating, "doubles", None)),
            "doubles_verified": _rating_display(getattr(rating, "doubles_verified", None)),
            "doubles_provisional": getattr(rating, "is_doubles_provisional", None),
        },
        "snapshot": {
            "player_metadata_updated_at": _to_date_str(getattr(snapshot, "player_metadata_updated_at", None)),
            "matches_updated_at": _to_date_str(getattr(snapshot, "matches_updated_at", None)),
            "matches_scope": getattr(snapshot, "matches_scope", None),
            "matches_start_date": getattr(snapshot, "matches_start_date", None),
            "matches_end_date": getattr(snapshot, "matches_end_date", None),
            "matches_count": getattr(snapshot, "matches_count", None),
        },
        "raw_player_metadata": snapshot_json,
    }


def _series_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    numeric = [float(row["rating"]) for row in rows if isinstance(row.get("rating"), (int, float))]
    if not numeric:
        return {"count": len(rows), "first": None, "latest": None, "delta": None}
    first = numeric[0]
    latest = numeric[-1]
    return {
        "count": len(rows),
        "first": first,
        "latest": latest,
        "delta": latest - first,
    }


def get_player_rating_series(
    runtime: AppRuntime,
    dupr_id: int,
    rating_type: str,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, Any]:
    requested = rating_type.lower()
    allowed = {"both": ["SINGLES", "DOUBLES"], "singles": ["SINGLES"], "doubles": ["DOUBLES"]}
    types = allowed.get(requested)
    if types is None:
        raise ValueError("rating_type must be both, singles, or doubles")

    with Session(runtime.engine) as sess:
        stmt = (
            select(PlayerRatingHistory)
            .where(PlayerRatingHistory.player_dupr_id == dupr_id)
            .order_by(
                PlayerRatingHistory.rating_type.asc(),
                PlayerRatingHistory.rating_date.asc(),
                PlayerRatingHistory.row_index.asc(),
            )
        )
        rows = sess.execute(stmt).scalars().all()

    series: dict[str, list[dict[str, Any]]] = {"singles": [], "doubles": []}
    for row in rows:
        if row.rating_type.upper() not in types:
            continue
        date_str = row.rating_date
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue
        item = {
            "id": row.id,
            "rating_type": row.rating_type.lower(),
            "rating_date": row.rating_date,
            "match_date": row.match_date,
            "rating": row.rating,
            "changed_by_admin": row.changed_by_admin,
            "row_index": row.row_index,
            "scope_start_date": row.scope_start_date,
            "scope_end_date": row.scope_end_date,
            "fetched_at": _to_date_str(row.fetched_at),
            "raw": _safe_json_load(row.rating_history_json),
        }
        series[row.rating_type.lower()].append(item)

    stats = {
        "singles": _series_stats(series["singles"]),
        "doubles": _series_stats(series["doubles"]),
    }
    trends = {
        "singles": sparkline([item.get("rating") for item in series["singles"]]),
        "doubles": sparkline([item.get("rating") for item in series["doubles"]]),
    }

    return {
        "dupr_id": dupr_id,
        "type_requested": requested,
        "start_date": start_date,
        "end_date": end_date,
        "series": series,
        "stats": stats,
        "trends": trends,
    }


def _player_names(players: list[Player]) -> str:
    return ", ".join([p.full_name for p in players])


def get_player_match_summaries(
    runtime: AppRuntime,
    dupr_id: int,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, Any]:
    with Session(runtime.engine) as sess:
        player = sess.execute(select(Player).where(Player.dupr_id == dupr_id)).scalar_one_or_none()
        if player is None:
            return {"dupr_id": dupr_id, "rows": []}

        raw_rows = sess.execute(
            select(PlayerMatchRaw).where(PlayerMatchRaw.player_dupr_id == dupr_id)
        ).scalars().all()

        raw_by_match: dict[int, dict[str, Any]] = {}
        for raw in raw_rows:
            payload = _safe_json_load(raw.match_json)
            if isinstance(payload, dict):
                raw_by_match[raw.match_id] = payload

        summaries: list[dict[str, Any]] = []
        seen: set[int] = set()
        for player_team in player.match_teams:
            match = player_team.match
            if match is None or match.match_id in seen:
                continue
            seen.add(match.match_id)

            match_date = _to_date_str(match.date)
            if start_date and match_date < start_date:
                continue
            if end_date and match_date > end_date:
                continue

            my_team = None
            for team in match.teams:
                ids = {p.dupr_id for p in team.players}
                if dupr_id in ids:
                    my_team = team
                    break
            if my_team is None:
                continue

            opp_teams = [team for team in match.teams if team.id != my_team.id]
            partner = _player_names([p for p in my_team.players if p.dupr_id != dupr_id]) or "-"
            opponents = _player_names([p for team in opp_teams for p in team.players]) or "-"
            opp_score = opp_teams[0].score1 if opp_teams else None
            scoreline = f"{my_team.score1}-{opp_score}" if opp_score is not None else str(my_team.score1)

            raw_payload = raw_by_match.get(match.match_id, {})
            event_format = raw_payload.get("eventFormat") or getattr(match, "event_format", None) or "unknown"
            status = raw_payload.get("status") or "unknown"

            summaries.append(
                {
                    "match_id": match.match_id,
                    "date": match_date,
                    "event_name": match.name,
                    "format": event_format,
                    "source": match.match_source,
                    "result": "W" if my_team.is_winner else "L",
                    "partner": partner,
                    "opponents": opponents,
                    "scoreline": scoreline,
                    "status": status,
                    "raw_available": match.match_id in raw_by_match,
                }
            )

    summaries.sort(key=lambda row: (row["date"], row["match_id"]), reverse=True)
    return {"dupr_id": dupr_id, "rows": summaries}


def get_match_detail(runtime: AppRuntime, match_id: int, player_dupr_id: int | None = None) -> dict[str, Any] | None:
    with Session(runtime.engine) as sess:
        match = sess.execute(select(Match).where(Match.match_id == match_id)).scalar_one_or_none()
        if match is None:
            return None

        raw_stmt = select(PlayerMatchRaw).where(PlayerMatchRaw.match_id == match_id)
        if player_dupr_id is not None:
            raw_stmt = raw_stmt.where(PlayerMatchRaw.player_dupr_id == player_dupr_id)
        raw_stmt = raw_stmt.order_by(PlayerMatchRaw.fetched_at.desc())
        raw = sess.execute(raw_stmt).scalars().first()

        raw_payload = _safe_json_load(raw.match_json if raw else None)

        teams: list[dict[str, Any]] = []
        for idx, team in enumerate(match.teams, start=1):
            teams.append(
                {
                    "team": idx,
                    "players": [p.full_name for p in team.players],
                    "score1": team.score1,
                    "score2": team.score2,
                    "score3": team.score3,
                    "winner": team.is_winner,
                }
            )

        return {
            "match_id": match.match_id,
            "name": match.name,
            "date": _to_date_str(match.date),
            "match_type": match.match_type,
            "match_source": match.match_source,
            "match_score_added": match.match_score_added,
            "event_format": (raw_payload or {}).get("eventFormat"),
            "status": (raw_payload or {}).get("status"),
            "created": (raw_payload or {}).get("created"),
            "modified": (raw_payload or {}).get("modified"),
            "client_name": (raw_payload or {}).get("clientName"),
            "teams": teams,
            "raw": raw_payload,
            "raw_player_dupr_id": raw.player_dupr_id if raw else None,
        }


def list_raw_metadata(
    runtime: AppRuntime,
    kind: str,
    player_dupr_id: int | None,
    match_id: int | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    k = kind.lower()
    with Session(runtime.engine) as sess:
        if k == "player":
            stmt = select(PlayerMetadataSnapshot).order_by(PlayerMetadataSnapshot.id.desc())
            if player_dupr_id is not None:
                stmt = stmt.where(PlayerMetadataSnapshot.player_dupr_id == player_dupr_id)
            rows = sess.execute(stmt.offset(offset).limit(limit)).scalars().all()
            items = [
                {
                    "id": row.id,
                    "player_dupr_id": row.player_dupr_id,
                    "player_full_name": row.player_full_name,
                    "player_metadata_updated_at": _to_date_str(row.player_metadata_updated_at),
                    "matches_updated_at": _to_date_str(row.matches_updated_at),
                    "payload": _safe_json_load(row.player_metadata_json),
                }
                for row in rows
            ]
        elif k == "match":
            stmt = select(PlayerMatchRaw).order_by(PlayerMatchRaw.id.desc())
            if player_dupr_id is not None:
                stmt = stmt.where(PlayerMatchRaw.player_dupr_id == player_dupr_id)
            if match_id is not None:
                stmt = stmt.where(PlayerMatchRaw.match_id == match_id)
            rows = sess.execute(stmt.offset(offset).limit(limit)).scalars().all()
            items = [
                {
                    "id": row.id,
                    "player_dupr_id": row.player_dupr_id,
                    "match_id": row.match_id,
                    "fetched_at": _to_date_str(row.fetched_at),
                    "payload": _safe_json_load(row.match_json),
                }
                for row in rows
            ]
        elif k == "rating":
            stmt = select(PlayerRatingHistory).order_by(PlayerRatingHistory.id.desc())
            if player_dupr_id is not None:
                stmt = stmt.where(PlayerRatingHistory.player_dupr_id == player_dupr_id)
            rows = sess.execute(stmt.offset(offset).limit(limit)).scalars().all()
            items = [
                {
                    "id": row.id,
                    "player_dupr_id": row.player_dupr_id,
                    "rating_type": row.rating_type,
                    "rating_date": row.rating_date,
                    "match_date": row.match_date,
                    "rating": row.rating,
                    "scope_start_date": row.scope_start_date,
                    "scope_end_date": row.scope_end_date,
                    "fetched_at": _to_date_str(row.fetched_at),
                    "payload": _safe_json_load(row.rating_history_json),
                }
                for row in rows
            ]
        else:
            raise ValueError("kind must be one of: player, match, rating")

    return {
        "kind": k,
        "limit": limit,
        "offset": offset,
        "rows": items,
        "count": len(items),
        "player_dupr_id": player_dupr_id,
        "match_id": match_id,
    }
