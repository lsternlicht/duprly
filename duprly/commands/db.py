from __future__ import annotations

from duprly.compat_click import click
from duprly.runtime import AppRuntime
from duprly.services import db_stats, rebuild_match_detail
from duprly.ui import UI


@click.group(help="Database utilities and maintenance tasks.")
def db() -> None:
    pass


@db.command("stats", help="Show row counts for key tables.")
@click.pass_obj
def db_stats_cmd(runtime: AppRuntime) -> None:
    ui = UI(no_color=runtime.no_color)
    result = db_stats(runtime)
    if runtime.json_output:
        ui.print_json(result)
        return

    ui.table(
        "Database Stats",
        ["Players", "Matches", "Ratings", "Match Detail"],
        [[result["players"], result["matches"], result["ratings"], result["match_detail"]]],
    )


@db.command("rebuild-match-detail", help="Rebuild the denormalized match_detail table.")
@click.pass_obj
def db_rebuild_match_detail_cmd(runtime: AppRuntime) -> None:
    ui = UI(no_color=runtime.no_color)
    result = rebuild_match_detail(runtime, ui)
    if runtime.json_output:
        ui.print_json(result)
        return

    ui.table("match_detail Rebuilt", ["Created", "Skipped"], [[result["created"], result["skipped"]]])
