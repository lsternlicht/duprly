from __future__ import annotations

import os
import sys

from duprly.compat_click import HAS_RICH_CLICK, click
from duprly.interactive import run_interactive
from duprly.runtime import AppRuntime
from duprly.ui import UI

from .commands.auth import auth_group, auth_import_browser_token
from .commands.browse import browse, browse_matches, browse_player
from .commands.explore import explore
from .commands.db import db, db_rebuild_match_detail_cmd, db_stats_cmd
from .commands.doctor import doctor_check, doctor_group
from .commands.export import export, export_workbook_cmd
from .commands.sync import (
    sync,
    sync_all_cmd,
    sync_matches_cmd,
    sync_players_cmd,
    sync_ratings_cmd,
)

if HAS_RICH_CLICK:
    click.rich_click.COMMAND_GROUPS = {
        "duprly": [
            {
                "name": "Core Workflows",
                "commands": ["sync", "browse", "explore", "export", "db", "doctor", "auth", "import-browser-token"],
            },
            {
                "name": "Legacy Compatibility",
                "commands": [
                    "get-data",
                    "get-all-players",
                    "get-all-player-matches",
                    "get-player",
                    "get-matches",
                    "update-ratings",
                    "build-match-detail",
                    "stats",
                    "write-excel",
                    "delete-player",
                    "test-db",
                ],
            },
        ],
        "duprly.py": [
            {
                "name": "Core Workflows",
                "commands": ["sync", "browse", "explore", "export", "db", "doctor", "auth", "import-browser-token"],
            },
            {
                "name": "Legacy Compatibility",
                "commands": [
                    "get-data",
                    "get-all-players",
                    "get-all-player-matches",
                    "get-player",
                    "get-matches",
                    "update-ratings",
                    "build-match-detail",
                    "stats",
                    "write-excel",
                    "delete-player",
                    "test-db",
                ],
            },
        ],
    }


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=(
        "DUPR data CLI with interactive workflows, progress feedback, and rich help.\n\n"
        "Examples:\n"
        "  duprly sync all\n"
        "  duprly sync matches --all-players\n"
        "  duprly browse lookup --entity player --query \"aidan bai\"\n"
        "  duprly browse rating-history 6886613721 --type both\n"
        "  duprly explore\n"
        "  duprly explore player 6886613721 ratings --type both\n"
        "  duprly explore web --open\n"
        "  duprly import-browser-token --browser comet --domain dupr.com\n"
        "  duprly auth import-browser-token --browser safari\n"
        "  duprly export club-players \"NYC Pickleball\"\n"
        "  duprly db stats"
    ),
)
@click.option("--verbose", is_flag=True, help="Enable debug logs.")
@click.option("--quiet", is_flag=True, help="Reduce logs to warnings/errors.")
@click.option("--no-color", is_flag=True, help="Disable color output.")
@click.option("--json", "json_output", is_flag=True, help="Emit command results as JSON.")
@click.option("--config", "config_path", type=click.Path(exists=True), help="Path to dotenv config file.")
@click.option(
    "--interactive/--no-interactive",
    default=True,
    show_default=True,
    help="Open interactive menu when no subcommand is provided.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: bool,
    quiet: bool,
    no_color: bool,
    json_output: bool,
    config_path: str | None,
    interactive: bool,
) -> None:
    runtime = AppRuntime(
        verbose=verbose,
        quiet=quiet,
        no_color=no_color,
        json_output=json_output,
        config_path=config_path,
        interactive=interactive,
    )
    runtime.setup_logging()
    ctx.obj = runtime

    if ctx.invoked_subcommand is None:
        if interactive and sys.stdin.isatty() and sys.stdout.isatty():
            run_interactive(runtime)
            return
        click.echo(ctx.get_help())


cli.add_command(sync)
cli.add_command(browse)
cli.add_command(explore)
cli.add_command(export)
cli.add_command(db)
cli.add_command(doctor_group, name="doctor")
cli.add_command(auth_group, name="auth")
cli.add_command(auth_import_browser_token, name="import-browser-token")


# Legacy compatibility aliases.
def _legacy_warning() -> None:
    ui = UI()
    ui.print(
        "[deprecated] This command name is kept for compatibility. Use the task-based command tree shown in --help.",
        style="yellow",
    )


@cli.command("get-data", help="[deprecated] Alias for 'sync all'.")
@click.pass_context
def legacy_get_data(ctx: click.Context) -> None:
    _legacy_warning()
    ctx.invoke(sync_all_cmd, club_id=None, start_date=None, end_date=None)


@cli.command("get-all-players", help="[deprecated] Alias for 'sync players'.")
@click.pass_context
def legacy_get_all_players(ctx: click.Context) -> None:
    _legacy_warning()
    ctx.invoke(sync_players_cmd, club_id=None)


@cli.command("get-all-player-matches", help="[deprecated] Alias for 'sync matches --all-players'.")
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.pass_context
def legacy_get_all_player_matches(ctx: click.Context, start_date: str | None, end_date: str | None) -> None:
    _legacy_warning()
    ctx.invoke(sync_matches_cmd, dupr_id=None, all_players=True, start_date=start_date, end_date=end_date)


@cli.command("get-player", help="[deprecated] Alias for 'browse player'.")
@click.argument("pid")
@click.pass_context
def legacy_get_player(ctx: click.Context, pid: str) -> None:
    _legacy_warning()
    ctx.invoke(browse_player, dupr_id=pid, save=True)


@cli.command("get-matches", help="[deprecated] Alias for 'browse matches'.")
@click.argument("dupr_id")
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", help="End date (YYYY-MM-DD).")
@click.pass_context
def legacy_get_matches(ctx: click.Context, dupr_id: str, start_date: str | None, end_date: str | None) -> None:
    _legacy_warning()
    ctx.invoke(
        browse_matches,
        dupr_id=dupr_id,
        start_date=start_date,
        end_date=end_date,
        persist=True,
    )


@cli.command("update-ratings", help="[deprecated] Alias for 'sync ratings'.")
@click.option("--all", "all_players", is_flag=True, help="Refresh all players.")
@click.pass_context
def legacy_update_ratings(ctx: click.Context, all_players: bool) -> None:
    _legacy_warning()
    ctx.invoke(sync_ratings_cmd, all_players=all_players)


@cli.command("build-match-detail", help="[deprecated] Alias for 'db rebuild-match-detail'.")
@click.pass_context
def legacy_build_match_detail(ctx: click.Context) -> None:
    _legacy_warning()
    ctx.invoke(db_rebuild_match_detail_cmd)


@cli.command("stats", help="[deprecated] Alias for 'db stats'.")
@click.pass_context
def legacy_stats(ctx: click.Context) -> None:
    _legacy_warning()
    ctx.invoke(db_stats_cmd)


@cli.command("write-excel", help="[deprecated] Alias for 'export workbook'.")
@click.option("--output", default="dupr.xlsx", show_default=True)
@click.pass_context
def legacy_write_excel(ctx: click.Context, output: str) -> None:
    _legacy_warning()
    ctx.invoke(export_workbook_cmd, output=output)


@cli.command("delete-player", help="[deprecated] Legacy no-op retained for compatibility.")
@click.argument("pid")
def legacy_delete_player(pid: str) -> None:
    _legacy_warning()
    click.echo(f"delete-player is not implemented in the new CLI. Requested PID: {pid}")


@cli.command("test-db", help="[deprecated] Alias for 'doctor check'.")
@click.pass_context
def legacy_test_db(ctx: click.Context) -> None:
    _legacy_warning()
    ctx.invoke(doctor_check, check_api=False)


def main() -> None:
    cli(prog_name="duprly")


if __name__ == "__main__":
    main()
