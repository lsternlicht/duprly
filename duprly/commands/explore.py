from __future__ import annotations

import sys
import subprocess
import webbrowser
import importlib.util
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from duprly.compat_click import click
from duprly.datasette_config import build_datasette_metadata
from duprly.explore_services import (
    export_data,
    get_match_detail,
    get_player_match_summaries,
    get_player_overview,
    get_player_rating_series,
    list_players,
    list_raw_metadata,
)
from duprly.runtime import AppRuntime
from duprly.ui import UI


_DATE_FMT = "%Y-%m-%d"


def _validate_date_option(value: str | None, option_name: str) -> str | None:
    if value is None:
        return None
    try:
        datetime.strptime(value, _DATE_FMT)
    except ValueError as err:
        raise click.ClickException(f"Invalid {option_name}: {value}. Expected YYYY-MM-DD.") from err
    return value


def _handle_service_error(err: Exception) -> None:
    msg = str(err)
    if "no such table" in msg.lower():
        raise click.ClickException("Local DB is missing required tables. Run `duprly sync all` first.") from err
    raise click.ClickException(msg) from err


def _trim_text(value: Any, width: int = 42) -> str:
    text = "" if value is None else str(value)
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."


def _maybe_export(
    ui: UI,
    data: Any,
    *,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
    default_prefix: str,
    default_format: str,
    render: bool = True,
) -> dict[str, Any] | None:
    wants_export = bool(export_format or output or clipboard)
    if not wants_export:
        return None

    fmt = (export_format or default_format).lower()
    if fmt not in {"csv", "json"}:
        raise click.ClickException("--export must be one of: csv, json")

    result = export_data(
        data=data,
        export_format=fmt,
        output=output,
        clipboard=clipboard,
        default_prefix=default_prefix,
    )

    if render:
        ui.table(
            "Export",
            ["Format", "File", "Clipboard", "Mechanism", "Reason", "Bytes"],
            [
                [
                    result["format"],
                    result["output"] or "(none)",
                    "ok" if result["clipboard_ok"] else ("n/a" if not clipboard else "failed"),
                    result["clipboard_mechanism"],
                    result["clipboard_reason"] or "",
                    result["bytes"],
                ]
            ],
        )
    return result


def _render_player_overview(ui: UI, detail: dict[str, Any]) -> None:
    snapshot = detail.get("snapshot", {})
    ratings = detail.get("ratings", {})
    ui.table(
        "Player Summary",
        ["Name", "DUPR ID", "Gender", "Age", "Email", "Phone", "Club ID"],
        [
            [
                detail.get("name", ""),
                detail.get("dupr_id", ""),
                detail.get("gender", ""),
                detail.get("age", ""),
                detail.get("email", ""),
                detail.get("phone", ""),
                detail.get("club_id", ""),
            ]
        ],
    )
    ui.table(
        "Current Ratings",
        [
            "Singles",
            "Singles Verified",
            "Singles Provisional",
            "Doubles",
            "Doubles Verified",
            "Doubles Provisional",
        ],
        [
            [
                ratings.get("singles", "NR"),
                ratings.get("singles_verified", "NR"),
                ratings.get("singles_provisional", "unknown"),
                ratings.get("doubles", "NR"),
                ratings.get("doubles_verified", "NR"),
                ratings.get("doubles_provisional", "unknown"),
            ]
        ],
    )
    ui.table(
        "Snapshots",
        ["Metadata Updated", "Matches Updated", "Scope", "Start", "End", "Count"],
        [
            [
                snapshot.get("player_metadata_updated_at", ""),
                snapshot.get("matches_updated_at", ""),
                snapshot.get("matches_scope", ""),
                snapshot.get("matches_start_date", ""),
                snapshot.get("matches_end_date", ""),
                snapshot.get("matches_count", ""),
            ]
        ],
    )


def _render_ratings(ui: UI, result: dict[str, Any]) -> list[dict[str, Any]]:
    stats = result.get("stats", {})
    trends = result.get("trends", {})
    series = result.get("series", {})

    rows = []
    for key in ["singles", "doubles"]:
        s = stats.get(key, {})
        rows.append(
            [
                key,
                s.get("count", 0),
                s.get("first", ""),
                s.get("latest", ""),
                s.get("delta", ""),
                trends.get(key, "(no data)"),
            ]
        )
    ui.table("Rating Trend", ["Type", "Points", "First", "Latest", "Delta", "Spark"], rows)

    flat_rows: list[dict[str, Any]] = []
    for key in ["singles", "doubles"]:
        for row in series.get(key, []):
            flat_rows.append(
                {
                    "rating_type": key,
                    "rating_date": row.get("rating_date"),
                    "match_date": row.get("match_date"),
                    "rating": row.get("rating"),
                    "changed_by_admin": row.get("changed_by_admin"),
                    "row_index": row.get("row_index"),
                    "scope_start_date": row.get("scope_start_date"),
                    "scope_end_date": row.get("scope_end_date"),
                    "fetched_at": row.get("fetched_at"),
                    "raw": row.get("raw"),
                }
            )

    flat_rows.sort(key=lambda r: (r.get("rating_date") or "", r.get("row_index") or 0, r.get("rating_type", "")))
    if flat_rows:
        sample = flat_rows[:50]
        ui.table(
            "Rating Points",
            ["#", "Type", "Rating Date", "Match Date", "Rating", "Admin"],
            [
                [
                    i + 1,
                    row.get("rating_type", ""),
                    row.get("rating_date", ""),
                    row.get("match_date", ""),
                    row.get("rating", ""),
                    row.get("changed_by_admin", ""),
                ]
                for i, row in enumerate(sample)
            ],
        )
        if len(flat_rows) > len(sample):
            ui.print(f"Showing first {len(sample)} of {len(flat_rows)} rating points.", style="yellow")
    else:
        ui.print("No rating history rows found for this scope.", style="yellow")

    return flat_rows


def _render_match_summaries(ui: UI, result: dict[str, Any], *, max_rows: int = 80) -> list[dict[str, Any]]:
    rows = result.get("rows", [])
    if not rows:
        ui.print("No saved matches found for this player/scope.", style="yellow")
        return []

    sample = rows[:max_rows]
    ui.table(
        "Saved Match Summaries",
        ["#", "Date", "Match ID", "Event", "Fmt", "Src", "W/L", "Partner", "Opponents", "Score", "Raw"],
        [
            [
                i + 1,
                row.get("date", ""),
                row.get("match_id", ""),
                _trim_text(row.get("event_name", ""), 34),
                row.get("format", ""),
                row.get("source", ""),
                row.get("result", ""),
                _trim_text(row.get("partner", ""), 24),
                _trim_text(row.get("opponents", ""), 26),
                row.get("scoreline", ""),
                "yes" if row.get("raw_available") else "no",
            ]
            for i, row in enumerate(sample)
        ],
    )
    if len(rows) > len(sample):
        ui.print(f"Showing first {len(sample)} of {len(rows)} matches.", style="yellow")
    return rows


def _render_match_detail(ui: UI, detail: dict[str, Any]) -> None:
    ui.table(
        "Match Detail",
        [
            "Match ID",
            "Date",
            "Event",
            "Type",
            "Source",
            "Format",
            "Status",
            "Created",
            "Modified",
        ],
        [
            [
                detail.get("match_id", ""),
                detail.get("date", ""),
                detail.get("name", ""),
                detail.get("match_type", ""),
                detail.get("match_source", ""),
                detail.get("event_format", ""),
                detail.get("status", ""),
                detail.get("created", ""),
                detail.get("modified", ""),
            ]
        ],
    )

    teams = detail.get("teams", [])
    if teams:
        ui.table(
            "Teams",
            ["Team", "Players", "Score 1", "Score 2", "Score 3", "Winner"],
            [
                [
                    row.get("team", ""),
                    ", ".join(row.get("players", [])),
                    row.get("score1", ""),
                    row.get("score2", ""),
                    row.get("score3", ""),
                    row.get("winner", ""),
                ]
                for row in teams
            ],
        )


def _datasette_cmd(
    runtime: AppRuntime,
    host: str,
    port: int,
    metadata_path: Path,
    template_dir: Path,
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "datasette",
        str(runtime.db_path.resolve()),
        "-h",
        host,
        "-p",
        str(port),
        "--metadata",
        str(metadata_path),
        "--template-dir",
        str(template_dir),
        "--setting",
        "default_page_size",
        "50",
        "--setting",
        "max_returned_rows",
        "20000",
        "--setting",
        "allow_csv_stream",
        "true",
        "--setting",
        "allow_download",
        "true",
    ]


def _ensure_datasette_runtime() -> None:
    if importlib.util.find_spec("datasette") is None:
        raise click.ClickException(
            "Datasette is not installed in this environment. Install it with "
            "`./.venv/bin/pip install datasette sqlite-utils`."
        )
    if importlib.util.find_spec("pkg_resources") is None:
        raise click.ClickException(
            "Datasette requires `pkg_resources` from setuptools. Install it with "
            "`./.venv/bin/python -m pip install 'setuptools<81'`."
        )


def _run_datasette(runtime: AppRuntime, ui: UI, host: str, port: int, open_browser: bool) -> dict[str, Any]:
    _ensure_datasette_runtime()
    has_vega = importlib.util.find_spec("datasette_vega") is not None
    # Open DB once before launching Datasette so additive schema updates/backfills are applied.
    _ = runtime.engine
    db_name = runtime.db_path.stem
    metadata = build_datasette_metadata(db_name)
    template_dir = Path(__file__).resolve().parent.parent / "datasette_templates"
    if not template_dir.exists():
        raise click.ClickException(f"Datasette template directory not found: {template_dir}")

    fd, temp_metadata_path = tempfile.mkstemp(prefix="duprly-datasette-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    metadata_path = Path(temp_metadata_path)

    url = f"http://{host}:{port}/"
    if open_browser:
        webbrowser.open(url)

    ui.print(f"Starting web explorer on {url}", style="green")
    ui.print("Press Ctrl+C to stop Datasette.", style="yellow")
    if not has_vega:
        ui.print(
            "datasette-vega plugin not installed; trend queries still work in table mode. "
            "Install with `./.venv/bin/python -m pip install datasette-vega` for richer chart options.",
            style="yellow",
        )

    try:
        rc = subprocess.call(_datasette_cmd(runtime, host, port, metadata_path, template_dir))
    except KeyboardInterrupt:
        rc = 0
    finally:
        try:
            metadata_path.unlink(missing_ok=True)
        except Exception:
            pass

    if rc not in (0, None):
        raise click.ClickException(f"Datasette exited with code {rc}.")
    return {
        "url": url,
        "host": host,
        "port": port,
        "opened": open_browser,
        "database": db_name,
        "template_dir": str(template_dir),
        "metadata_generated": True,
        "vega_plugin": has_vega,
    }


def _show_player_detail_command(
    runtime: AppRuntime,
    ui: UI,
    dupr_id: int,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> dict[str, Any]:
    try:
        detail = get_player_overview(runtime, dupr_id)
    except Exception as err:
        _handle_service_error(err)

    if detail is None:
        raise click.ClickException(f"No saved player found with DUPR ID {dupr_id}.")

    if not runtime.json_output:
        _render_player_overview(ui, detail)

    export_result = _maybe_export(
        ui,
        detail,
        export_format=export_format,
        output=output,
        clipboard=clipboard,
        default_prefix=f"explore_player_{dupr_id}",
        default_format="json",
        render=not runtime.json_output,
    )
    if export_result:
        detail = {**detail, "export": export_result}
    return detail


def _show_player_ratings_command(
    runtime: AppRuntime,
    ui: UI,
    dupr_id: int,
    rating_type: str,
    start_date: str | None,
    end_date: str | None,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> dict[str, Any]:
    _validate_date_option(start_date, "--start-date")
    _validate_date_option(end_date, "--end-date")

    try:
        result = get_player_rating_series(runtime, dupr_id, rating_type, start_date, end_date)
    except Exception as err:
        _handle_service_error(err)

    flat_rows = _render_ratings(ui, result) if not runtime.json_output else []
    export_payload: Any = {
        "dupr_id": result.get("dupr_id"),
        "type_requested": result.get("type_requested"),
        "start_date": result.get("start_date"),
        "end_date": result.get("end_date"),
        "stats": result.get("stats"),
        "trends": result.get("trends"),
        "rows": [
            {
                "rating_type": row.get("rating_type"),
                "rating_date": row.get("rating_date"),
                "match_date": row.get("match_date"),
                "rating": row.get("rating"),
                "changed_by_admin": row.get("changed_by_admin"),
                "row_index": row.get("row_index"),
                "scope_start_date": row.get("scope_start_date"),
                "scope_end_date": row.get("scope_end_date"),
                "fetched_at": row.get("fetched_at"),
            }
            for row in flat_rows
        ],
    }
    if runtime.json_output:
        export_payload = result

    export_result = _maybe_export(
        ui,
        export_payload,
        export_format=export_format,
        output=output,
        clipboard=clipboard,
        default_prefix=f"explore_rating_{dupr_id}_{rating_type}",
        default_format="csv",
        render=not runtime.json_output,
    )

    if export_result:
        result = {**result, "export": export_result}
    return result


def _show_player_matches_command(
    runtime: AppRuntime,
    ui: UI,
    dupr_id: int,
    start_date: str | None,
    end_date: str | None,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> dict[str, Any]:
    _validate_date_option(start_date, "--start-date")
    _validate_date_option(end_date, "--end-date")

    try:
        result = get_player_match_summaries(runtime, dupr_id, start_date, end_date)
    except Exception as err:
        _handle_service_error(err)

    if not runtime.json_output:
        _render_match_summaries(ui, result)

    export_result = _maybe_export(
        ui,
        result,
        export_format=export_format,
        output=output,
        clipboard=clipboard,
        default_prefix=f"explore_player_{dupr_id}_matches",
        default_format="csv",
        render=not runtime.json_output,
    )
    if export_result:
        result = {**result, "export": export_result}
    return result


def _show_match_detail_command(
    runtime: AppRuntime,
    ui: UI,
    match_id: int,
    player_dupr_id: int | None,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> dict[str, Any]:
    try:
        detail = get_match_detail(runtime, match_id, player_dupr_id)
    except Exception as err:
        _handle_service_error(err)

    if detail is None:
        raise click.ClickException(f"No saved match found with match_id {match_id}.")

    if not runtime.json_output:
        _render_match_detail(ui, detail)

    export_result = _maybe_export(
        ui,
        detail,
        export_format=export_format,
        output=output,
        clipboard=clipboard,
        default_prefix=f"explore_match_{match_id}",
        default_format="json",
        render=not runtime.json_output,
    )
    if export_result:
        detail = {**detail, "export": export_result}
    return detail


def _show_raw_metadata_command(
    runtime: AppRuntime,
    ui: UI,
    kind: str,
    player_dupr_id: int | None,
    match_id: int | None,
    limit: int,
    offset: int,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> dict[str, Any]:
    try:
        result = list_raw_metadata(runtime, kind, player_dupr_id, match_id, limit, offset)
    except Exception as err:
        _handle_service_error(err)

    if not runtime.json_output:
        rows = result.get("rows", [])
        if not rows:
            ui.print("No raw metadata rows found for this scope.", style="yellow")
        else:
            ui.table(
                "Raw Metadata",
                ["#", "Kind", "ID", "Player DUPR", "Match ID", "Rating Date", "Fetched At"],
                [
                    [
                        i + 1,
                        kind,
                        row.get("id", ""),
                        row.get("player_dupr_id", ""),
                        row.get("match_id", ""),
                        row.get("rating_date", ""),
                        row.get("fetched_at", ""),
                    ]
                    for i, row in enumerate(rows)
                ],
            )

    export_result = _maybe_export(
        ui,
        result,
        export_format=export_format,
        output=output,
        clipboard=clipboard,
        default_prefix=f"explore_raw_{kind}",
        default_format="json",
        render=not runtime.json_output,
    )
    if export_result:
        result = {**result, "export": export_result}
    return result


def _interactive_player_ratings(runtime: AppRuntime, ui: UI, dupr_id: int) -> None:
    rating_type = ui.ask("Rating type", choices=["both", "singles", "doubles"], default="both")
    start_date = ui.ask("Start date (optional YYYY-MM-DD)", default="").strip() or None
    end_date = ui.ask("End date (optional YYYY-MM-DD)", default="").strip() or None

    _validate_date_option(start_date, "start date")
    _validate_date_option(end_date, "end date")

    result = _show_player_ratings_command(
        runtime,
        ui,
        dupr_id,
        rating_type,
        start_date,
        end_date,
        export_format=None,
        output=None,
        clipboard=False,
    )

    flat_rows: list[dict[str, Any]] = []
    for key in ["singles", "doubles"]:
        for row in result.get("series", {}).get(key, []):
            flat_rows.append({"rating_type": key, **row})
    flat_rows.sort(key=lambda r: (r.get("rating_date") or "", r.get("row_index") or 0, r.get("rating_type") or ""))

    if not flat_rows:
        return

    while True:
        choice = ui.ask("Inspect rating row #, [e]xport, [b]ack", default="b").strip().lower()
        if choice == "b":
            return
        if choice == "e":
            fmt = ui.ask("Export format", choices=["csv", "json"], default="csv")
            out = ui.ask("Output path (blank for default)", default="").strip() or None
            use_clip = ui.confirm("Copy export to clipboard?", default=False)
            _maybe_export(
                ui,
                result,
                export_format=fmt,
                output=out,
                clipboard=use_clip,
                default_prefix=f"explore_rating_{dupr_id}_{rating_type}",
                default_format="csv",
            )
            continue
        if not choice.isdigit():
            ui.print("Invalid selection.", style="yellow")
            continue

        idx = int(choice) - 1
        if idx < 0 or idx >= len(flat_rows):
            ui.print("Selection out of range.", style="yellow")
            continue
        ui.print_json(flat_rows[idx].get("raw"))


def _interactive_match_detail(runtime: AppRuntime, ui: UI, match_id: int, player_dupr_id: int | None) -> None:
    detail = _show_match_detail_command(
        runtime,
        ui,
        match_id,
        player_dupr_id,
        export_format=None,
        output=None,
        clipboard=False,
    )

    while True:
        action = ui.ask("Action", choices=["1", "2", "b"], default="b")
        if action == "b":
            return
        if action == "1":
            raw = detail.get("raw")
            if raw is None:
                ui.print("Raw payload unavailable for this match.", style="yellow")
            else:
                ui.print_json(raw)
        if action == "2":
            fmt = ui.ask("Export format", choices=["json", "csv"], default="json")
            out = ui.ask("Output path (blank for default)", default="").strip() or None
            use_clip = ui.confirm("Copy export to clipboard?", default=False)
            _maybe_export(
                ui,
                detail,
                export_format=fmt,
                output=out,
                clipboard=use_clip,
                default_prefix=f"explore_match_{match_id}",
                default_format="json",
            )


def _interactive_player_matches(runtime: AppRuntime, ui: UI, dupr_id: int) -> None:
    start_date = ui.ask("Start date (optional YYYY-MM-DD)", default="").strip() or None
    end_date = ui.ask("End date (optional YYYY-MM-DD)", default="").strip() or None
    _validate_date_option(start_date, "start date")
    _validate_date_option(end_date, "end date")

    try:
        result = get_player_match_summaries(runtime, dupr_id, start_date, end_date)
    except Exception as err:
        _handle_service_error(err)
        return

    rows = result.get("rows", [])
    if not rows:
        ui.print("No saved matches found for this player/scope.", style="yellow")
        return

    page = 0
    page_size = 15
    while True:
        start = page * page_size
        end = start + page_size
        page_rows = rows[start:end]
        if not page_rows and page > 0:
            page -= 1
            continue

        ui.table(
            f"Saved Match Summaries (showing {start + 1}-{start + len(page_rows)} of {len(rows)})",
            ["#", "Date", "Match ID", "Event", "Fmt", "Src", "W/L", "Partner", "Opponents", "Score", "Raw"],
            [
                [
                    start + i + 1,
                    row.get("date", ""),
                    row.get("match_id", ""),
                    _trim_text(row.get("event_name", ""), 34),
                    row.get("format", ""),
                    row.get("source", ""),
                    row.get("result", ""),
                    _trim_text(row.get("partner", ""), 24),
                    _trim_text(row.get("opponents", ""), 26),
                    row.get("scoreline", ""),
                    "yes" if row.get("raw_available") else "no",
                ]
                for i, row in enumerate(page_rows)
            ],
        )

        choice = ui.ask("Open match #, [n]ext, [p]rev, [e]xport, [b]ack", default="b").strip().lower()
        if choice == "b":
            return
        if choice == "n":
            if end < len(rows):
                page += 1
            continue
        if choice == "p":
            if page > 0:
                page -= 1
            continue
        if choice == "e":
            fmt = ui.ask("Export format", choices=["csv", "json"], default="csv")
            out = ui.ask("Output path (blank for default)", default="").strip() or None
            use_clip = ui.confirm("Copy export to clipboard?", default=False)
            _maybe_export(
                ui,
                result,
                export_format=fmt,
                output=out,
                clipboard=use_clip,
                default_prefix=f"explore_player_{dupr_id}_matches",
                default_format="csv",
            )
            continue
        if not choice.isdigit():
            ui.print("Invalid selection.", style="yellow")
            continue

        idx = int(choice) - 1
        if idx < 0 or idx >= len(rows):
            ui.print("Selection out of range.", style="yellow")
            continue

        _interactive_match_detail(runtime, ui, int(rows[idx]["match_id"]), dupr_id)


def _interactive_player_detail(runtime: AppRuntime, ui: UI, dupr_id: int) -> None:
    detail = _show_player_detail_command(
        runtime,
        ui,
        dupr_id,
        export_format=None,
        output=None,
        clipboard=False,
    )

    while True:
        ui.table(
            "Player Actions",
            ["#", "Action"],
            [
                ["1", "View rating over time"],
                ["2", "View match history"],
                ["3", "View raw player metadata JSON"],
                ["4", "Export current view"],
                ["b", "Back"],
            ],
        )
        action = ui.ask("Choose action", default="b").strip().lower()
        if action == "b":
            return
        if action == "1":
            _interactive_player_ratings(runtime, ui, dupr_id)
        elif action == "2":
            _interactive_player_matches(runtime, ui, dupr_id)
        elif action == "3":
            ui.print_json(detail.get("raw_player_metadata"))
        elif action == "4":
            fmt = ui.ask("Export format", choices=["json", "csv"], default="json")
            out = ui.ask("Output path (blank for default)", default="").strip() or None
            use_clip = ui.confirm("Copy export to clipboard?", default=False)
            _maybe_export(
                ui,
                detail,
                export_format=fmt,
                output=out,
                clipboard=use_clip,
                default_prefix=f"explore_player_{dupr_id}",
                default_format="json",
            )
        else:
            ui.print("Invalid action.", style="yellow")


def _interactive_players(runtime: AppRuntime, ui: UI) -> None:
    query = ui.ask("Search player name or DUPR ID (optional)", default="").strip() or None
    limit = 12
    offset = 0

    while True:
        try:
            result = list_players(runtime, query=query, limit=limit, offset=offset)
        except Exception as err:
            _handle_service_error(err)

        rows = result.get("rows", [])
        total = result.get("total", 0)
        if not rows and offset > 0:
            offset = max(0, offset - limit)
            continue

        if rows:
            ui.table(
                f"Players (offset {offset}, showing {len(rows)} of {total})",
                ["#", "Name", "DUPR ID", "Singles", "Doubles", "Metadata Updated"],
                [
                    [
                        i + 1,
                        _trim_text(row.get("name", ""), 26),
                        row.get("dupr_id", ""),
                        row.get("singles", ""),
                        row.get("doubles", ""),
                        row.get("metadata_updated_at", ""),
                    ]
                    for i, row in enumerate(rows)
                ],
            )
        else:
            ui.print("No players found.", style="yellow")

        choice = ui.ask("Choose #, [n]ext, [p]rev, [s]earch, [e]xport, [b]ack", default="b").strip().lower()
        if choice == "b":
            return
        if choice == "s":
            query = ui.ask("Search player name or DUPR ID (optional)", default="").strip() or None
            offset = 0
            continue
        if choice == "e":
            _maybe_export(
                ui,
                result,
                export_format="csv",
                output=None,
                clipboard=False,
                default_prefix="explore_players",
                default_format="csv",
            )
            continue
        if choice == "n":
            if offset + limit < total:
                offset += limit
            continue
        if choice == "p":
            offset = max(0, offset - limit)
            continue
        if not choice.isdigit():
            ui.print("Invalid selection.", style="yellow")
            continue

        idx = int(choice) - 1
        if idx < 0 or idx >= len(rows):
            ui.print("Selection out of range.", style="yellow")
            continue

        _interactive_player_detail(runtime, ui, int(rows[idx]["dupr_id"]))


def _interactive_matches(runtime: AppRuntime, ui: UI) -> None:
    value = ui.ask("Player DUPR ID for match history", default="").strip()
    if not value.isdigit():
        ui.print("DUPR ID must be numeric.", style="yellow")
        return
    _interactive_player_matches(runtime, ui, int(value))


def _interactive_ratings(runtime: AppRuntime, ui: UI) -> None:
    value = ui.ask("Player DUPR ID for rating history", default="").strip()
    if not value.isdigit():
        ui.print("DUPR ID must be numeric.", style="yellow")
        return
    _interactive_player_ratings(runtime, ui, int(value))


def _interactive_raw(runtime: AppRuntime, ui: UI) -> None:
    kind = ui.ask("Raw metadata kind", choices=["player", "match", "rating"], default="player")
    player_text = ui.ask("Filter by player DUPR ID (optional)", default="").strip()
    match_text = ui.ask("Filter by match_id (optional)", default="").strip()
    player_dupr_id = int(player_text) if player_text.isdigit() else None
    match_id = int(match_text) if match_text.isdigit() else None
    limit = 20
    offset = 0

    while True:
        result = _show_raw_metadata_command(
            runtime,
            ui,
            kind,
            player_dupr_id,
            match_id,
            limit,
            offset,
            export_format=None,
            output=None,
            clipboard=False,
        )
        rows = result.get("rows", [])
        if not rows and offset > 0:
            offset = max(0, offset - limit)
            continue

        choice = ui.ask("Inspect row #, [n]ext, [p]rev, [e]xport, [b]ack", default="b").strip().lower()
        if choice == "b":
            return
        if choice == "n":
            if len(rows) == limit:
                offset += limit
            continue
        if choice == "p":
            offset = max(0, offset - limit)
            continue
        if choice == "e":
            fmt = ui.ask("Export format", choices=["json", "csv"], default="json")
            out = ui.ask("Output path (blank for default)", default="").strip() or None
            use_clip = ui.confirm("Copy export to clipboard?", default=False)
            _show_raw_metadata_command(
                runtime,
                ui,
                kind,
                player_dupr_id,
                match_id,
                limit,
                offset,
                export_format=fmt,
                output=out,
                clipboard=use_clip,
            )
            continue
        if not choice.isdigit():
            ui.print("Invalid selection.", style="yellow")
            continue

        idx = int(choice) - 1
        if idx < 0 or idx >= len(rows):
            ui.print("Selection out of range.", style="yellow")
            continue

        ui.print_json(rows[idx].get("payload"))


def run_explore_interactive(runtime: AppRuntime, ui: UI | None = None) -> None:
    ui = ui or UI(no_color=runtime.no_color)
    while True:
        ui.table(
            "Explore Saved Data",
            ["#", "Action"],
            [
                ["1", "Players"],
                ["2", "Matches"],
                ["3", "Rating History"],
                ["4", "Raw Metadata"],
                ["5", "Open Web Explorer"],
                ["b", "Back"],
            ],
        )
        choice = ui.ask("Select action", default="b").strip().lower()
        if choice == "b":
            return

        try:
            if choice == "1":
                _interactive_players(runtime, ui)
            elif choice == "2":
                _interactive_matches(runtime, ui)
            elif choice == "3":
                _interactive_ratings(runtime, ui)
            elif choice == "4":
                _interactive_raw(runtime, ui)
            elif choice == "5":
                host = ui.ask("Host", default="127.0.0.1")
                port_text = ui.ask("Port", default="8001")
                if not port_text.isdigit():
                    ui.print("Port must be numeric.", style="yellow")
                    continue
                open_browser = ui.confirm("Open browser now?", default=True)
                _run_datasette(runtime, ui, host=host, port=int(port_text), open_browser=open_browser)
            else:
                ui.print("Invalid action.", style="yellow")
        except Exception as err:
            if isinstance(err, click.ClickException):
                ui.print(f"Error: {err}", style="bold red")
            else:
                _handle_service_error(err)


@click.group(
    name="explore",
    invoke_without_command=True,
    help="Explore saved local data (interactive navigator, drill-down views, and exports).",
)
@click.pass_context
def explore(ctx: click.Context) -> None:
    runtime = ctx.obj
    if ctx.invoked_subcommand is not None:
        return

    if not isinstance(runtime, AppRuntime):
        raise click.ClickException("Runtime context missing.")

    ui = UI(no_color=runtime.no_color)
    if sys.stdin.isatty() and sys.stdout.isatty():
        run_explore_interactive(runtime, ui)
    else:
        click.echo(ctx.get_help())


@explore.command("players", help="List saved players with optional query/pagination.")
@click.option("--query", help="Filter by name or DUPR ID.")
@click.option("--limit", default=20, show_default=True, type=int)
@click.option("--offset", default=0, show_default=True, type=int)
@click.option("--export", "export_format", type=click.Choice(["csv", "json"]))
@click.option("--output", help="Output file path.")
@click.option("--clipboard", is_flag=True, help="Copy exported text to clipboard.")
@click.pass_obj
def explore_players_cmd(
    runtime: AppRuntime,
    query: str | None,
    limit: int,
    offset: int,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> None:
    ui = UI(no_color=runtime.no_color)
    try:
        result = list_players(runtime, query=query, limit=limit, offset=offset)
    except Exception as err:
        _handle_service_error(err)
        return

    if not runtime.json_output:
        rows = result.get("rows", [])
        if not rows:
            ui.print("No saved players found.", style="yellow")
        else:
            ui.table(
                "Saved Players",
                ["Name", "DUPR ID", "Gender", "Age", "Singles", "Doubles", "Metadata Updated"],
                [
                    [
                        row.get("name", ""),
                        row.get("dupr_id", ""),
                        row.get("gender", ""),
                        row.get("age", ""),
                        row.get("singles", ""),
                        row.get("doubles", ""),
                        row.get("metadata_updated_at", ""),
                    ]
                    for row in rows
                ],
            )

    export_result = _maybe_export(
        ui,
        result,
        export_format=export_format,
        output=output,
        clipboard=clipboard,
        default_prefix="explore_players",
        default_format="csv",
        render=not runtime.json_output,
    )
    if export_result:
        result = {**result, "export": export_result}
    if runtime.json_output:
        ui.print_json(result)


@explore.group("player", invoke_without_command=True, help="Inspect a saved player and drill into ratings/matches.")
@click.argument("dupr_id", type=int)
@click.option("--export", "export_format", type=click.Choice(["csv", "json"]))
@click.option("--output", help="Output file path.")
@click.option("--clipboard", is_flag=True, help="Copy exported text to clipboard.")
@click.pass_context
def explore_player_group(
    ctx: click.Context,
    dupr_id: int,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> None:
    if ctx.invoked_subcommand is not None:
        return

    runtime = ctx.obj
    if not isinstance(runtime, AppRuntime):
        raise click.ClickException("Runtime context missing.")

    ui = UI(no_color=runtime.no_color)
    detail = _show_player_detail_command(runtime, ui, dupr_id, export_format, output, clipboard)
    if runtime.json_output:
        ui.print_json(detail)


@explore_player_group.command("ratings", help="View saved rating history for this player.")
@click.option(
    "--type",
    "rating_type",
    type=click.Choice(["both", "singles", "doubles"]),
    default="both",
    show_default=True,
)
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.option("--export", "export_format", type=click.Choice(["csv", "json"]))
@click.option("--output", help="Output file path.")
@click.option("--clipboard", is_flag=True, help="Copy exported text to clipboard.")
@click.pass_context
def explore_player_ratings_cmd(
    ctx: click.Context,
    rating_type: str,
    start_date: str | None,
    end_date: str | None,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> None:
    runtime = ctx.obj
    if not isinstance(runtime, AppRuntime):
        raise click.ClickException("Runtime context missing.")

    dupr_id = int(ctx.parent.params["dupr_id"])
    ui = UI(no_color=runtime.no_color)
    result = _show_player_ratings_command(
        runtime,
        ui,
        dupr_id,
        rating_type,
        start_date,
        end_date,
        export_format,
        output,
        clipboard,
    )
    if runtime.json_output:
        ui.print_json(result)


@explore_player_group.command("matches", help="View saved match summaries for this player.")
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.option("--export", "export_format", type=click.Choice(["csv", "json"]))
@click.option("--output", help="Output file path.")
@click.option("--clipboard", is_flag=True, help="Copy exported text to clipboard.")
@click.pass_context
def explore_player_matches_cmd(
    ctx: click.Context,
    start_date: str | None,
    end_date: str | None,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> None:
    runtime = ctx.obj
    if not isinstance(runtime, AppRuntime):
        raise click.ClickException("Runtime context missing.")

    dupr_id = int(ctx.parent.params["dupr_id"])
    ui = UI(no_color=runtime.no_color)
    result = _show_player_matches_command(
        runtime,
        ui,
        dupr_id,
        start_date,
        end_date,
        export_format,
        output,
        clipboard,
    )
    if runtime.json_output:
        ui.print_json(result)


@explore.command("match", help="View one saved match and full detail.")
@click.argument("match_id", type=int)
@click.option("--player-dupr-id", type=int, help="Prefer raw payload associated to this player if available.")
@click.option("--export", "export_format", type=click.Choice(["csv", "json"]))
@click.option("--output", help="Output file path.")
@click.option("--clipboard", is_flag=True, help="Copy exported text to clipboard.")
@click.pass_obj
def explore_match_cmd(
    runtime: AppRuntime,
    match_id: int,
    player_dupr_id: int | None,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> None:
    ui = UI(no_color=runtime.no_color)
    detail = _show_match_detail_command(runtime, ui, match_id, player_dupr_id, export_format, output, clipboard)
    if runtime.json_output:
        ui.print_json(detail)


@explore.command("raw", help="Browse raw metadata snapshots (player/match/rating).")
@click.option("--kind", type=click.Choice(["player", "match", "rating"]), default="player", show_default=True)
@click.option("--player-dupr-id", type=int, help="Filter by player DUPR ID.")
@click.option("--match-id", type=int, help="Filter by match ID (for match kind).")
@click.option("--limit", default=25, show_default=True, type=int)
@click.option("--offset", default=0, show_default=True, type=int)
@click.option("--export", "export_format", type=click.Choice(["csv", "json"]))
@click.option("--output", help="Output file path.")
@click.option("--clipboard", is_flag=True, help="Copy exported text to clipboard.")
@click.pass_obj
def explore_raw_cmd(
    runtime: AppRuntime,
    kind: str,
    player_dupr_id: int | None,
    match_id: int | None,
    limit: int,
    offset: int,
    export_format: str | None,
    output: str | None,
    clipboard: bool,
) -> None:
    ui = UI(no_color=runtime.no_color)
    result = _show_raw_metadata_command(
        runtime,
        ui,
        kind,
        player_dupr_id,
        match_id,
        limit,
        offset,
        export_format,
        output,
        clipboard,
    )
    if runtime.json_output:
        ui.print_json(result)


@explore.command("web", help="Launch a local Datasette web explorer for dupr.sqlite.")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8001, type=int, show_default=True)
@click.option("--open/--no-open", "open_browser", default=True, show_default=True)
@click.pass_obj
def explore_web_cmd(runtime: AppRuntime, host: str, port: int, open_browser: bool) -> None:
    ui = UI(no_color=runtime.no_color)
    result = _run_datasette(runtime, ui, host=host, port=port, open_browser=open_browser)
    if runtime.json_output:
        ui.print_json(result)
