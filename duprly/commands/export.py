from __future__ import annotations

from duprly.compat_click import click
from duprly.runtime import AppRuntime
from duprly.services import export_club_players, export_rankings, export_workbook
from duprly.ui import UI


@click.group(help="Export data to JSON/Excel artifacts.")
def export() -> None:
    pass


@export.command("club-players", help="Search/select a club and export all players to JSON.")
@click.argument("club_query", required=False)
@click.option("--club-id", help="Bypass search and export by exact club ID.")
@click.option("--output", help="Output JSON file path.")
@click.option("--non-interactive", is_flag=True, help="Pick first search hit automatically.")
@click.pass_obj
def export_club_players_cmd(
    runtime: AppRuntime,
    club_query: str | None,
    club_id: str | None,
    output: str | None,
    non_interactive: bool,
) -> None:
    ui = UI(no_color=runtime.no_color)
    result = export_club_players(
        runtime,
        ui,
        club_query=club_query,
        club_id=club_id,
        output_path=output,
        non_interactive=non_interactive,
    )

    if runtime.json_output:
        ui.print_json(result)
        return

    ui.table(
        "Club Players Exported",
        ["Club", "ID", "Players", "Output"],
        [[result["club_name"], result["club_id"], result["players"], result["output"]]],
    )


@export.command("rankings", help="Export club ranking data to JSON.")
@click.argument("club_id")
@click.option("--output", help="Output JSON file path.")
@click.pass_obj
def export_rankings_cmd(runtime: AppRuntime, club_id: str, output: str | None) -> None:
    ui = UI(no_color=runtime.no_color)
    result = export_rankings(runtime, ui, club_id=club_id, output_path=output)

    if runtime.json_output:
        ui.print_json(result)
        return

    ui.table(
        "Rankings Exported",
        ["Club ID", "Players", "Output"],
        [[result["club_id"], result["players"], result["output"]]],
    )


@export.command("workbook", help="Export local DB contents into an Excel workbook.")
@click.option("--output", default="dupr.xlsx", show_default=True, help="Workbook file path.")
@click.pass_obj
def export_workbook_cmd(runtime: AppRuntime, output: str) -> None:
    ui = UI(no_color=runtime.no_color)
    result = export_workbook(runtime, ui, output_path=output)

    if runtime.json_output:
        ui.print_json(result)
        return

    ui.table(
        "Workbook Exported",
        ["Players", "Matches", "Output"],
        [[result["players"], result["matches"], result["output"]]],
    )
