from __future__ import annotations

import os

from duprly.compat_click import click
from duprly.runtime import AppRuntime
from duprly.services import extract_dupr_token_from_browser, set_access_token
from duprly.ui import UI


@click.group(help="Authentication helpers.")
def auth_group() -> None:
    pass


def run_import_browser_token(
    runtime: AppRuntime,
    ui: UI,
    browser: str,
    domain: str,
    cookie_name: str,
    token: str | None,
    save: bool,
) -> tuple[dict, str | None]:
    token_value = token or os.getenv("DUPR_ACCESS_TOKEN")
    if token_value:
        result = set_access_token(runtime, token_value, save=save)
        result.update(
            {
                "browser": "manual",
                "domain": domain,
                "cookie_name": cookie_name,
                "refresh_token_found": False,
            }
        )
    else:
        result = extract_dupr_token_from_browser(
            runtime,
            ui,
            browser=browser,
            domain=domain,
            cookie_name=cookie_name,
            save=save,
        )
    token_value = result.pop("token", None)
    return result, token_value


def render_import_browser_token(
    runtime: AppRuntime,
    ui: UI,
    result: dict,
    token: str | None,
    show_token: bool,
) -> None:
    if runtime.json_output:
        if show_token and token:
            result["token"] = token
        ui.print_json(result)
        return

    ui.table(
        "Browser Token Import",
        ["Browser", "Domain", "Saved", "Config", "Preview", "Expires (UTC)"],
        [
            [
                result["browser"],
                result["domain"],
                "yes" if result["saved"] else "no",
                result["config_path"],
                result["token_preview"],
                result["token_expires_at_utc"] or "unknown",
            ]
        ],
    )
    if show_token and token:
        ui.print(token)


@auth_group.command("import-browser-token", help="Extract DUPR auth token from browser cookies.")
@click.option(
    "--browser",
    type=click.Choice(["safari", "chrome", "chromium", "brave", "edge", "firefox", "comet"]),
    default="safari",
    show_default=True,
    help="Browser profile to inspect.",
)
@click.option("--domain", default="dupr.com", show_default=True, help="Cookie domain filter.")
@click.option("--cookie-name", default="dupr_access_token", show_default=True, help="Access-token cookie name.")
@click.option(
    "--token",
    help="Direct token value. If set, browser cookie lookup is skipped.",
)
@click.option("--save/--no-save", default=True, show_default=True, help="Persist token into ~/.duprly_config.")
@click.option("--show-token", is_flag=True, help="Print the full token value.")
@click.pass_obj
def auth_import_browser_token(
    runtime: AppRuntime,
    browser: str,
    domain: str,
    cookie_name: str,
    token: str | None,
    save: bool,
    show_token: bool,
) -> None:
    ui = UI(no_color=runtime.no_color)
    result, resolved_token = run_import_browser_token(
        runtime=runtime,
        ui=ui,
        browser=browser,
        domain=domain,
        cookie_name=cookie_name,
        token=token,
        save=save,
    )
    render_import_browser_token(runtime, ui, result, resolved_token, show_token)
