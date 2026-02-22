from __future__ import annotations

from duprly.compat_click import click
from duprly.runtime import AppRuntime
from duprly.services import doctor
from duprly.ui import UI


@click.group(help="Health checks for environment, DB, and optional API connectivity.")
def doctor_group() -> None:
    pass


@doctor_group.command("check", help="Run diagnostics.")
@click.option("--api", "check_api", is_flag=True, help="Include a live DUPR API profile check.")
@click.pass_obj
def doctor_check(runtime: AppRuntime, check_api: bool) -> None:
    ui = UI(no_color=runtime.no_color)
    result = doctor(runtime, ui, check_api=check_api)

    if runtime.json_output:
        ui.print_json(result)
        return

    rows = [[k, "ok" if v else "missing"] for k, v in result["checks"].items()]
    ui.table("Environment Checks", ["Check", "Status"], rows)

    if check_api:
        api = result["api"]
        ui.table(
            "API Check",
            ["Enabled", "Status", "OK"],
            [[api["enabled"], api["status"], api["ok"]]],
        )
