from __future__ import annotations

import os

from duprly.compat_click import click
from duprly.commands.auth import render_import_browser_token, run_import_browser_token
from duprly.commands.browse import run_lookup_workflow
from duprly.commands.explore import run_explore_interactive
from duprly.runtime import AppRuntime
from duprly.services import (
    interactive_quick_status,
    sync_all,
    sync_matches,
    sync_players,
)
from duprly.ui import UI, print_exception


def run_interactive(runtime: AppRuntime) -> None:
    ui = UI(no_color=runtime.no_color)

    status_rows = interactive_quick_status(runtime)
    ui.panel(
        "duprly",
        "Interactive mode. Choose a workflow to run, or quit.",
        style="green",
    )
    ui.table("Quick Status", ["Item", "Value"], status_rows)

    while True:
        ui.table(
            "Actions",
            ["#", "Action"],
            [
                ["1", "Sync all data"],
                ["2", "Sync players only"],
                ["3", "Sync matches for all DB players"],
                ["4", "Show help and examples"],
                ["5", "Lookup player/club"],
                ["6", "Import browser token"],
                ["7", "Explore saved data"],
                ["q", "Quit"],
            ],
        )

        choice = ui.ask("Select action", choices=["1", "2", "3", "4", "5", "6", "7", "q"], default="q")
        if choice == "q":
            ui.print("Goodbye.")
            return

        try:
            if choice == "1":
                club_id = ui.ask("Club ID", default=os.getenv("DUPR_CLUB_ID", ""))
                if not club_id:
                    raise click.ClickException("Club ID is required.")
                result = sync_all(runtime, ui, club_id=club_id, start_date=None, end_date=None)
                ui.table(
                    "Sync Complete",
                    ["Players", "Matches", "New Matches", "Ratings Updated"],
                    [
                        [
                            result["players"]["total"],
                            result["matches"]["total_matches"],
                            result["matches"]["inserted"],
                            result["ratings"]["updated"],
                        ]
                    ],
                )
            elif choice == "2":
                club_id = ui.ask("Club ID", default=os.getenv("DUPR_CLUB_ID", ""))
                if not club_id:
                    raise click.ClickException("Club ID is required.")
                result = sync_players(runtime, ui, club_id=club_id)
                ui.table(
                    "Players Synced",
                    ["Total", "Inserted", "Updated"],
                    [[result["total"], result["inserted"], result["updated"]]],
                )
            elif choice == "3":
                result = sync_matches(
                    runtime,
                    ui,
                    dupr_id=None,
                    all_players=True,
                    start_date=None,
                    end_date=None,
                )
                ui.table(
                    "Matches Synced",
                    ["Players", "Matches", "Inserted", "Skipped", "Failures"],
                    [
                        [
                            result["players_processed"],
                            result["total_matches"],
                            result["inserted"],
                            result["skipped"],
                            len(result["failures"]),
                        ]
                    ],
                )
            elif choice == "4":
                ui.print("Run `duprly --help` to view all commands.", style="bold cyan")
            elif choice == "5":
                entity = ui.ask("Lookup entity", choices=["player", "club"], default="player")
                run_lookup_workflow(
                    runtime=runtime,
                    ui=ui,
                    entity=entity,
                    limit=8,
                    query=None,
                    output=None,
                    start_date=None,
                    end_date=None,
                    no_download_matches=False,
                    no_download_rating_history=False,
                )
            elif choice == "6":
                browser = ui.ask(
                    "Browser",
                    choices=["safari", "chrome", "chromium", "brave", "edge", "firefox", "comet"],
                    default="safari",
                )
                domain = ui.ask("Cookie domain", default="dupr.com")
                save = ui.confirm("Save token into ~/.duprly_config?", default=True)
                show_token = ui.confirm("Show full token value?", default=False)
                result, token = run_import_browser_token(
                    runtime=runtime,
                    ui=ui,
                    browser=browser,
                    domain=domain,
                    cookie_name="dupr_access_token",
                    token=None,
                    save=save,
                )
                render_import_browser_token(
                    runtime=runtime,
                    ui=ui,
                    result=result,
                    token=token,
                    show_token=show_token,
                )
            elif choice == "7":
                run_explore_interactive(runtime, ui)
        except Exception as err:  # pragma: no cover - interactive branch
            print_exception(ui, err)
