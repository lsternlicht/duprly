from __future__ import annotations

import json
import sys

from duprly.autocomplete import lookup_with_suggestions
from duprly.compat_click import click
from duprly.runtime import AppRuntime
from duprly.services import (
    ensure_auth,
    export_profile_matches,
    fetch_matches,
    fetch_rating_history,
    fetch_player,
    resolve_lookup_selection,
    search_clubs,
)
from duprly.ui import UI


@click.group(help="Browse DUPR entities and inspect live results.")
def browse() -> None:
    pass


def _first_non_null(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _rating_display(value) -> str:
    if value is None:
        return "NR"
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized or normalized.upper() in {"NR", "-", "NONE", "NULL"}:
            return "NR"
        return normalized
    if isinstance(value, (int, float)):
        return f"{float(value):.3f}".rstrip("0").rstrip(".")
    return str(value)


def _extract_player_ratings(pdata: dict) -> dict[str, str]:
    ratings_obj = pdata.get("ratings")
    if not isinstance(ratings_obj, dict):
        ratings_obj = {}

    singles = _first_non_null(
        ratings_obj.get("singles"),
        pdata.get("singles"),
        pdata.get("singlesRating"),
        pdata.get("singleRating"),
    )
    doubles = _first_non_null(
        ratings_obj.get("doubles"),
        pdata.get("doubles"),
        pdata.get("doublesRating"),
        pdata.get("doubleRating"),
    )
    singles_verified = _first_non_null(
        ratings_obj.get("singlesVerified"),
        pdata.get("singlesVerified"),
        pdata.get("singlesRatingVerified"),
    )
    doubles_verified = _first_non_null(
        ratings_obj.get("doublesVerified"),
        pdata.get("doublesVerified"),
        pdata.get("doublesRatingVerified"),
    )
    singles_provisional = _first_non_null(
        ratings_obj.get("singlesProvisional"),
        pdata.get("singlesProvisional"),
        pdata.get("isSinglesProvisional"),
    )
    doubles_provisional = _first_non_null(
        ratings_obj.get("doublesProvisional"),
        pdata.get("doublesProvisional"),
        pdata.get("isDoublesProvisional"),
    )

    return {
        "singles": _rating_display(singles),
        "doubles": _rating_display(doubles),
        "singles_verified": _rating_display(singles_verified),
        "doubles_verified": _rating_display(doubles_verified),
        "singles_provisional": str(singles_provisional) if singles_provisional is not None else "unknown",
        "doubles_provisional": str(doubles_provisional) if doubles_provisional is not None else "unknown",
    }


def _player_location(pdata: dict) -> str:
    return (
        pdata.get("shortAddress")
        or pdata.get("locationText")
        or pdata.get("location")
        or pdata.get("city")
        or "unknown"
    )


def _render_player_panel(ui: UI, pdata: dict, save: bool) -> None:
    ratings = _extract_player_ratings(pdata)
    ui.table(
        "Player",
        ["Name", "ID", "DUPR", "Gender", "Age", "Location", "Saved"],
        [
            [
                pdata.get("fullName", "Unknown"),
                pdata.get("id", "Unknown"),
                pdata.get("duprId", "Unknown"),
                pdata.get("gender", "unknown"),
                pdata.get("age", "unknown"),
                _player_location(pdata),
                "yes" if save else "no",
            ]
        ],
    )
    ui.table(
        "Ratings",
        ["Singles", "Singles Verified", "Singles Prov", "Doubles", "Doubles Verified", "Doubles Prov"],
        [
            [
                ratings["singles"],
                ratings["singles_verified"],
                ratings["singles_provisional"],
                ratings["doubles"],
                ratings["doubles_verified"],
                ratings["doubles_provisional"],
            ]
        ],
    )


def _write_matches_output(output: str, matches: list[dict]) -> None:
    with open(output, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)


def _write_rating_history_output(output: str, result: dict) -> None:
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


@browse.command("player", help="Fetch a player by DUPR ID.")
@click.argument("dupr_id")
@click.option("--save/--no-save", default=True, help="Persist fetched player into local DB.")
@click.pass_obj
def browse_player(runtime: AppRuntime, dupr_id: str, save: bool) -> None:
    ui = UI(no_color=runtime.no_color)
    pdata = fetch_player(runtime, ui, dupr_id, persist=save)

    if runtime.json_output:
        ui.print_json(pdata)
        return

    _render_player_panel(ui, pdata, save=save)


@browse.command("matches", help="Fetch player match history by DUPR ID.")
@click.argument("dupr_id")
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.option("--output", help="Optional JSON output file path for full match payload.")
@click.option("--persist/--no-persist", default=True, help="Persist fetched matches into local DB.")
@click.pass_obj
def browse_matches(
    runtime: AppRuntime,
    dupr_id: str,
    start_date: str | None,
    end_date: str | None,
    output: str | None,
    persist: bool,
) -> None:
    ui = UI(no_color=runtime.no_color)
    result = fetch_matches(
        runtime,
        ui,
        dupr_id=dupr_id,
        start_date=start_date,
        end_date=end_date,
        persist=persist,
    )

    if output:
        _write_matches_output(output, result["matches"])

    if runtime.json_output:
        ui.print_json(result)
        return

    ui.table(
        "Match History",
        ["DUPR ID", "Scope", "Matches", "Persisted", "Inserted", "Skipped", "Raw I/U/D", "Snapshot"],
        [
            [
                result["dupr_id"],
                result["scope"],
                result["match_count"],
                "yes" if persist else "no",
                result["persisted"]["inserted"],
                result["persisted"]["skipped"],
                f"{result['raw_persisted']['inserted']}/{result['raw_persisted']['updated']}/{result['raw_persisted']['deleted']}",
                "yes" if result["snapshot_updated"] else "no",
            ]
        ],
    )
    if output:
        ui.print(f"Wrote full match metadata JSON: {output}", style="green")


@browse.command("rating-history", help="Fetch player rating history by DUPR ID.")
@click.argument("dupr_id")
@click.option(
    "--type",
    "rating_type",
    type=click.Choice(["both", "singles", "doubles"]),
    default="both",
    show_default=True,
    help="Rating history type to fetch.",
)
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.option("--output", help="Optional JSON output file path for full rating-history payload.")
@click.option("--persist/--no-persist", default=True, help="Persist fetched rating history into local DB.")
@click.pass_obj
def browse_rating_history(
    runtime: AppRuntime,
    dupr_id: str,
    rating_type: str,
    start_date: str | None,
    end_date: str | None,
    output: str | None,
    persist: bool,
) -> None:
    ui = UI(no_color=runtime.no_color)
    result = fetch_rating_history(
        runtime,
        ui,
        dupr_id=dupr_id,
        rating_type=rating_type,
        start_date=start_date,
        end_date=end_date,
        persist=persist,
    )

    if output:
        _write_rating_history_output(output, result)

    if runtime.json_output:
        ui.print_json(result)
        return

    singles_count = result["counts"].get("singles", 0)
    doubles_count = result["counts"].get("doubles", 0)
    singles_inserted = result["persisted"].get("singles", {}).get("inserted", 0)
    doubles_inserted = result["persisted"].get("doubles", {}).get("inserted", 0)
    ui.table(
        "Rating History",
        ["DUPR ID", "Type", "Range", "Singles", "Doubles", "Persisted", "Inserted S/D"],
        [
            [
                result["dupr_id"],
                result["type_requested"],
                f"{result['start_date']} to {result['end_date']}",
                singles_count,
                doubles_count,
                "yes" if persist else "no",
                f"{singles_inserted}/{doubles_inserted}",
            ]
        ],
    )
    if output:
        ui.print(f"Wrote full rating-history JSON: {output}", style="green")


@browse.command("clubs", help="Search clubs by name query.")
@click.argument("query")
@click.option("--limit", default=10, show_default=True, help="Max clubs to return.")
@click.pass_obj
def browse_clubs(runtime: AppRuntime, query: str, limit: int) -> None:
    ui = UI(no_color=runtime.no_color)
    clubs = search_clubs(runtime, ui, query, limit)

    if runtime.json_output:
        ui.print_json(clubs)
        return

    rows = []
    for club in clubs:
        rows.append(
            [
                club.get("clubName", "Unknown"),
                club.get("clubId", "Unknown"),
                club.get("shortAddress", ""),
            ]
        )
    ui.table("Club Search Results", ["Name", "ID", "Location"], rows)


def run_lookup_workflow(
    runtime: AppRuntime,
    ui: UI,
    entity: str | None,
    limit: int,
    query: str | None,
    output: str | None,
    start_date: str | None,
    end_date: str | None,
    no_download_matches: bool,
    no_download_rating_history: bool,
) -> dict:
    ensure_auth(runtime, ui)

    entity_choice = entity
    if entity_choice is None:
        entity_choice = ui.ask("Lookup entity", choices=["player", "club"], default="player")

    if entity_choice == "player":
        def search_fn(q: str, l: int) -> list[dict]:
            rc, hits = runtime.client.search_players(query=q, limit=l)
            if rc != 200:
                raise RuntimeError(f"Player search failed (HTTP {rc}).")
            return hits
    else:
        def search_fn(q: str, l: int) -> list[dict]:
            rc, hits = runtime.client.search_clubs(query=q, limit=l)
            if rc != 200:
                raise RuntimeError(f"Club search failed (HTTP {rc}).")
            return hits

    if not (sys.stdin.isatty() and sys.stdout.isatty()) and not query:
        raise click.ClickException("In non-interactive mode, provide --query for lookup.")

    try:
        selection = lookup_with_suggestions(
            ui=ui,
            entity=entity_choice,
            limit=limit,
            search_func=search_fn,
            query=query,
        )
    except Exception as err:
        raise click.ClickException(str(err)) from err
    if not selection:
        raise click.ClickException(f"No {entity_choice} selected.")

    resolved = resolve_lookup_selection(runtime, ui, entity_choice, selection, persist=True)
    result: dict = resolved

    if entity_choice == "player":
        pdata = resolved["player"]
        if not runtime.json_output:
            _render_player_panel(ui, pdata, save=True)

        download_matches = False
        if not no_download_matches:
            if sys.stdin.isatty() and sys.stdout.isatty():
                download_matches = ui.confirm("Download all match metadata now?", default=True)
            else:
                download_matches = True

        if download_matches:
            match_result = fetch_matches(
                runtime,
                ui,
                dupr_id=str(pdata.get("id")),
                start_date=start_date,
                end_date=end_date,
                persist=True,
            )
            result["match_download"] = match_result
            if output:
                _write_matches_output(output, match_result["matches"])
                result["match_output"] = output

            if not runtime.json_output:
                ui.table(
                    "Match Download Complete",
                    ["Scope", "Matches", "Inserted", "Skipped", "Raw I/U/D", "Snapshot"],
                    [
                        [
                            match_result["scope"],
                            match_result["match_count"],
                            match_result["persisted"]["inserted"],
                            match_result["persisted"]["skipped"],
                            f"{match_result['raw_persisted']['inserted']}/{match_result['raw_persisted']['updated']}/{match_result['raw_persisted']['deleted']}",
                            "yes" if match_result["snapshot_updated"] else "no",
                        ]
                    ],
                )
                if output:
                    ui.print(f"Wrote full match metadata JSON: {output}", style="green")

        download_rating_history = False
        if not no_download_rating_history:
            if sys.stdin.isatty() and sys.stdout.isatty():
                download_rating_history = ui.confirm("Download rating history now?", default=True)
            else:
                download_rating_history = True

        if download_rating_history:
            rating_result = fetch_rating_history(
                runtime,
                ui,
                dupr_id=str(pdata.get("id")),
                rating_type="both",
                start_date=start_date,
                end_date=end_date,
                persist=True,
            )
            result["rating_history_download"] = rating_result
            if not runtime.json_output:
                ui.table(
                    "Rating History Download Complete",
                    ["Range", "Singles", "Doubles", "Inserted S/D"],
                    [
                        [
                            f"{rating_result['start_date']} to {rating_result['end_date']}",
                            rating_result["counts"].get("singles", 0),
                            rating_result["counts"].get("doubles", 0),
                            f"{rating_result['persisted'].get('singles', {}).get('inserted', 0)}/"
                            f"{rating_result['persisted'].get('doubles', {}).get('inserted', 0)}",
                        ]
                    ],
                )
    else:
        club = resolved["club"]
        if not runtime.json_output:
            ui.table(
                "Club",
                ["Name", "ID", "Location"],
                [[club.get("clubName", "Unknown"), club.get("clubId", "Unknown"), club.get("shortAddress", "")]],
            )

    return result


@browse.command("lookup", help="Live lookup by player/club name with suggestions.")
@click.option("--entity", type=click.Choice(["player", "club"]), help="Lookup entity type.")
@click.option("--limit", default=8, show_default=True, help="Max suggestions to return.")
@click.option("--query", help="Initial query text (required in non-interactive mode).")
@click.option("--output", help="Output JSON file path for downloaded match metadata.")
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.option("--no-download-matches", is_flag=True, help="Skip match download after selecting a player.")
@click.option("--no-download-rating-history", is_flag=True, help="Skip rating-history download after selecting a player.")
@click.pass_obj
def browse_lookup(
    runtime: AppRuntime,
    entity: str | None,
    limit: int,
    query: str | None,
    output: str | None,
    start_date: str | None,
    end_date: str | None,
    no_download_matches: bool,
    no_download_rating_history: bool,
) -> None:
    ui = UI(no_color=runtime.no_color)
    result = run_lookup_workflow(
        runtime=runtime,
        ui=ui,
        entity=entity,
        limit=limit,
        query=query,
        output=output,
        start_date=start_date,
        end_date=end_date,
        no_download_matches=no_download_matches,
        no_download_rating_history=no_download_rating_history,
    )
    if runtime.json_output:
        ui.print_json(result)
        return


@browse.command("profile-matches", help="Fetch your own profile matches and export to JSON.")
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.option("--output", default="matches.json", show_default=True, help="Output JSON path.")
@click.pass_obj
def browse_profile_matches(
    runtime: AppRuntime,
    start_date: str | None,
    end_date: str | None,
    output: str,
) -> None:
    ui = UI(no_color=runtime.no_color)
    result = export_profile_matches(runtime, ui, start_date=start_date, end_date=end_date, output_path=output)

    if runtime.json_output:
        ui.print_json(result)
        return

    range_display = "ALL"
    if result["start_date"] or result["end_date"]:
        range_display = f"{result['start_date']} to {result['end_date']}"
    ui.table(
        "Profile Matches Exported",
        ["DUPR ID", "Matches", "Output", "Range"],
        [[result["dupr_id"], result["matches"], result["output"], range_display]],
    )
