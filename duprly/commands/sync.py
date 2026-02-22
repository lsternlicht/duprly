from __future__ import annotations

import os

from duprly.compat_click import click
from duprly.runtime import AppRuntime
from duprly.services import sync_all, sync_matches, sync_players, sync_ratings
from duprly.ui import UI


@click.group(help="Synchronize data from DUPR into your local database.")
def sync() -> None:
    pass


@sync.command("players", help="Sync all players for a club into the local DB.")
@click.option("--club-id", help="DUPR club ID (defaults to DUPR_CLUB_ID env var).")
@click.pass_obj
def sync_players_cmd(runtime: AppRuntime, club_id: str | None) -> None:
    ui = UI(no_color=runtime.no_color)
    club_id = club_id or os.getenv("DUPR_CLUB_ID")
    if not club_id:
        raise click.ClickException("Provide --club-id or set DUPR_CLUB_ID.")

    result = sync_players(runtime, ui, club_id)
    if runtime.json_output:
        ui.print_json(result)
        return

    ui.table(
        "Players Synced",
        ["Club", "Total", "Inserted", "Updated"],
        [[result["club_id"], result["total"], result["inserted"], result["updated"]]],
    )


@sync.command("matches", help="Sync match history for one player or all players in DB.")
@click.option("--dupr-id", help="Player DUPR ID.")
@click.option("--all-players", is_flag=True, help="Sync matches for all players in local DB.")
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.pass_obj
def sync_matches_cmd(
    runtime: AppRuntime,
    dupr_id: str | None,
    all_players: bool,
    start_date: str | None,
    end_date: str | None,
) -> None:
    ui = UI(no_color=runtime.no_color)
    result = sync_matches(
        runtime,
        ui,
        dupr_id=dupr_id,
        all_players=all_players,
        start_date=start_date,
        end_date=end_date,
    )

    if runtime.json_output:
        ui.print_json(result)
        return

    ui.table(
        "Matches Synced",
        ["Players", "Matches", "Inserted", "Skipped", "Failures", "Range"],
        [
            [
                result["players_processed"],
                result["total_matches"],
                result["inserted"],
                result["skipped"],
                len(result["failures"]),
                f"{result['start_date']} to {result['end_date']}",
            ]
        ],
    )


@sync.command("ratings", help="Refresh player ratings.")
@click.option("--all", "all_players", is_flag=True, help="Refresh ratings for all players.")
@click.pass_obj
def sync_ratings_cmd(runtime: AppRuntime, all_players: bool) -> None:
    ui = UI(no_color=runtime.no_color)
    result = sync_ratings(runtime, ui, all_players=all_players)

    if runtime.json_output:
        ui.print_json(result)
        return

    ui.table(
        "Ratings Synced",
        ["Mode", "Requested", "Updated", "Failures"],
        [[result["mode"], result["requested"], result["updated"], len(result["failed"])]],
    )


@sync.command("all", help="Run players, matches, and ratings sync in sequence.")
@click.option("--club-id", help="DUPR club ID (defaults to DUPR_CLUB_ID env var).")
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.pass_obj
def sync_all_cmd(
    runtime: AppRuntime,
    club_id: str | None,
    start_date: str | None,
    end_date: str | None,
) -> None:
    ui = UI(no_color=runtime.no_color)
    club_id = club_id or os.getenv("DUPR_CLUB_ID")
    if not club_id:
        raise click.ClickException("Provide --club-id or set DUPR_CLUB_ID.")

    result = sync_all(runtime, ui, club_id=club_id, start_date=start_date, end_date=end_date)

    if runtime.json_output:
        ui.print_json(result)
        return

    rows = [
        [
            result["players"]["total"],
            result["matches"]["total_matches"],
            result["matches"]["inserted"],
            result["ratings"]["updated"],
        ]
    ]
    ui.table("Sync Complete", ["Players", "Matches", "New Matches", "Ratings Updated"], rows)
