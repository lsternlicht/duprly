from __future__ import annotations

from typing import Any

from datasette import hookimpl
from datasette.utils.asgi import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from duprly.compat_click import click
from duprly.dupr_db import Player
from duprly.runtime import AppRuntime
from duprly.services import (
    fetch_matches,
    fetch_player,
    fetch_rating_history,
    search_players,
)
from duprly.ui import UI


def _truthy(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _friendly_error_message(message: str) -> str:
    msg = str(message or "").strip()
    lowered = msg.lower()
    if "http 401" in lowered or "authentication failed" in lowered:
        return (
            f"{msg} Auth looks missing/expired for this Datasette process. "
            "Set DUPR_ACCESS_TOKEN or run `duprly import-browser-token --browser comet --domain dupr.com`, "
            "then restart `duprly explore web`."
        )
    return msg


def _player_rating_value(payload: dict[str, Any], key: str) -> Any:
    ratings = payload.get("ratings")
    if isinstance(ratings, dict) and key in ratings:
        return ratings.get(key)
    return payload.get(key)


def _existing_player_ids(runtime: AppRuntime, ids: list[int]) -> set[int]:
    if not ids:
        return set()
    with Session(runtime.engine) as sess:
        rows = sess.execute(select(Player.dupr_id).where(Player.dupr_id.in_(ids))).all()
    return {int(row[0]) for row in rows if row and row[0] is not None}


async def search_players_remote(request, datasette):
    query = str(request.args.get("q") or "").strip()
    limit_text = str(request.args.get("limit") or "8").strip()
    try:
        limit = int(limit_text)
    except ValueError:
        limit = 8
    limit = max(1, min(limit, 25))

    # Keep API usage bounded while allowing direct numeric lookups by ID.
    if not query or (len(query) < 2 and not query.isdigit()):
        return Response.json(
            {
                "ok": True,
                "result": {
                    "query": query,
                    "limit": limit,
                    "hits": [],
                },
            },
            status=200,
        )

    runtime = AppRuntime(verbose=False, quiet=True, no_color=True, json_output=True, interactive=False)
    runtime.setup_logging()
    ui = UI(no_color=True)

    try:
        hits = search_players(runtime, ui, query=query, limit=limit)
    except click.ClickException as err:
        return Response.json({"ok": False, "error": _friendly_error_message(str(err))}, status=400)
    except Exception as err:  # pragma: no cover - defensive runtime guard
        return Response.json({"ok": False, "error": _friendly_error_message(str(err))}, status=500)

    player_ids: list[int] = []
    for item in hits:
        pid = item.get("id") or item.get("duprId")
        if pid is None:
            continue
        try:
            player_ids.append(int(pid))
        except (TypeError, ValueError):
            continue
    existing_ids = _existing_player_ids(runtime, player_ids)

    normalized_hits: list[dict[str, Any]] = []
    for item in hits:
        pid = item.get("id") or item.get("duprId")
        if pid is None:
            continue
        pid_text = str(pid).strip()
        if not pid_text.isdigit():
            continue
        full_name = str(item.get("fullName") or "Unknown").strip()
        normalized_hits.append(
            {
                "id": pid_text,
                "full_name": full_name,
                "dupr_code": item.get("duprId"),
                "short_address": item.get("shortAddress") or "",
                "singles": _player_rating_value(item, "singles"),
                "doubles": _player_rating_value(item, "doubles"),
                "already_saved": int(pid_text) in existing_ids,
                "label": f"{full_name} [{pid_text}]",
            }
        )

    return Response.json(
        {
            "ok": True,
            "result": {
                "query": query,
                "limit": limit,
                "hits": normalized_hits,
            },
        },
        status=200,
    )


async def import_player(request, datasette):
    dupr_id = str(request.args.get("dupr_id") or "").strip()
    if not dupr_id.isdigit():
        return Response.json(
            {
                "ok": False,
                "error": "Missing or invalid 'dupr_id' (numeric required).",
            },
            status=400,
        )

    include_rating_history = _truthy(request.args.get("include_rating_history"), default=False)
    include_matches = _truthy(request.args.get("include_matches"), default=False)
    rating_type = str(request.args.get("rating_type") or "doubles").strip().lower()
    if rating_type not in {"both", "singles", "doubles"}:
        rating_type = "doubles"
    start_date = str(request.args.get("start_date") or "").strip() or None
    end_date = str(request.args.get("end_date") or "").strip() or None

    runtime = AppRuntime(verbose=False, quiet=True, no_color=True, json_output=True, interactive=False)
    runtime.setup_logging()
    ui = UI(no_color=True)

    with Session(runtime.engine) as sess:
        existed_before = sess.execute(select(Player.id).where(Player.dupr_id == int(dupr_id))).scalar_one_or_none() is not None

    result: dict[str, Any] = {
        "dupr_id": dupr_id,
        "include_rating_history": include_rating_history,
        "include_matches": include_matches,
        "rating_type": rating_type,
        "start_date": start_date,
        "end_date": end_date,
    }
    warnings: list[str] = []

    try:
        player = fetch_player(runtime, ui, dupr_id, persist=True)
        result["player"] = {
            "id": player.get("id"),
            "full_name": player.get("fullName"),
            "dupr_code": player.get("duprId"),
            "short_address": player.get("shortAddress"),
            "singles": _player_rating_value(player, "singles"),
            "doubles": _player_rating_value(player, "doubles"),
        }
        result["added"] = not existed_before
        result["already_saved"] = existed_before

        if include_rating_history:
            try:
                ratings = fetch_rating_history(
                    runtime,
                    ui,
                    dupr_id=dupr_id,
                    rating_type=rating_type,
                    start_date=start_date,
                    end_date=end_date,
                    persist=True,
                )
                result["rating_history"] = {
                    "types_fetched": ratings.get("types_fetched"),
                    "counts": ratings.get("counts"),
                    "start_date": ratings.get("start_date"),
                    "end_date": ratings.get("end_date"),
                    "persisted": ratings.get("persisted"),
                    "fallback": ratings.get("fallback"),
                }
            except click.ClickException as err:
                warnings.append(f"Rating history sync failed: {err}")
                result["rating_history_error"] = str(err)

        if include_matches:
            try:
                matches = fetch_matches(
                    runtime,
                    ui,
                    dupr_id=dupr_id,
                    start_date=None,
                    end_date=None,
                    persist=True,
                )
                result["matches"] = {
                    "scope": matches.get("scope"),
                    "match_count": matches.get("match_count"),
                    "persisted": matches.get("persisted"),
                    "raw_persisted": matches.get("raw_persisted"),
                }
            except click.ClickException as err:
                warnings.append(f"Match sync failed: {err}")
                result["matches_error"] = str(err)

        return Response.json(
            {
                "ok": True,
                "partial": bool(warnings),
                "warnings": warnings,
                "result": result,
            },
            status=200,
        )
    except click.ClickException as err:
        return Response.json({"ok": False, "error": _friendly_error_message(str(err)), "result": result}, status=400)
    except Exception as err:  # pragma: no cover - defensive runtime guard
        return Response.json({"ok": False, "error": _friendly_error_message(str(err)), "result": result}, status=500)


async def request_player_data(request, datasette):
    """
    Fetch and persist fresh DUPR data for one player from within Datasette.
    """
    dupr_id = str(request.args.get("dupr_id") or "").strip()
    if not dupr_id.isdigit():
        return Response.json(
            {
                "ok": False,
                "error": "Missing or invalid 'dupr_id' (numeric required).",
            },
            status=400,
        )

    rating_type = str(request.args.get("rating_type") or "doubles").strip().lower()
    if rating_type not in {"both", "singles", "doubles"}:
        rating_type = "doubles"

    start_date = str(request.args.get("start_date") or "").strip() or None
    end_date = str(request.args.get("end_date") or "").strip() or None
    include_matches = _truthy(request.args.get("include_matches"), default=False)

    runtime = AppRuntime(verbose=False, quiet=True, no_color=True, json_output=True, interactive=False)
    runtime.setup_logging()
    ui = UI(no_color=True)

    result: dict[str, Any] = {
        "dupr_id": dupr_id,
        "rating_type": rating_type,
        "start_date": start_date,
        "end_date": end_date,
        "include_matches": include_matches,
    }

    try:
        player = fetch_player(runtime, ui, dupr_id, persist=True)
        warnings: list[str] = []

        if include_matches:
            try:
                matches = fetch_matches(runtime, ui, dupr_id=dupr_id, start_date=None, end_date=None, persist=True)
                result["matches"] = {
                    "scope": matches.get("scope"),
                    "match_count": matches.get("match_count"),
                    "persisted": matches.get("persisted"),
                    "raw_persisted": matches.get("raw_persisted"),
                }
            except click.ClickException as err:
                result["matches_error"] = str(err)
                warnings.append(f"Match sync failed: {err}")

        ratings = fetch_rating_history(
            runtime,
            ui,
            dupr_id=dupr_id,
            rating_type=rating_type,
            start_date=start_date,
            end_date=end_date,
            persist=True,
        )
        result["player"] = {
            "id": player.get("id"),
            "full_name": player.get("fullName"),
            "dupr_id": player.get("duprId"),
        }
        result["rating_history"] = {
            "types_fetched": ratings.get("types_fetched"),
            "counts": ratings.get("counts"),
            "start_date": ratings.get("start_date"),
            "end_date": ratings.get("end_date"),
            "persisted": ratings.get("persisted"),
            "fallback": ratings.get("fallback"),
        }

        return Response.json(
            {
                "ok": True,
                "partial": bool(warnings),
                "warnings": warnings,
                "result": result,
            },
            status=200,
        )
    except click.ClickException as err:
        return Response.json({"ok": False, "error": _friendly_error_message(str(err)), "result": result}, status=400)
    except Exception as err:  # pragma: no cover - defensive runtime guard
        return Response.json({"ok": False, "error": _friendly_error_message(str(err)), "result": result}, status=500)


@hookimpl
def register_routes(datasette):
    return [
        (r"^/-/duprly/search-players$", search_players_remote),
        (r"^/-/duprly/import-player$", import_player),
        (r"^/-/duprly/request-player-data$", request_player_data),
    ]
