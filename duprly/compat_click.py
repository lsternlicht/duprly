"""Click compatibility layer with optional rich-click support."""

from __future__ import annotations

try:
    import rich_click as click  # type: ignore

    HAS_RICH_CLICK = True
    click.rich_click.USE_RICH_MARKUP = True
    click.rich_click.SHOW_ARGUMENTS = True
    click.rich_click.SHOW_METAVARS_COLUMN = False
    click.rich_click.OPTION_ENVVAR_FIRST = True
    click.rich_click.STYLE_HELPTEXT_FIRST_LINE = "bold"
    click.rich_click.STYLE_OPTION = "bold cyan"
    click.rich_click.STYLE_SWITCH = "bold green"
    click.rich_click.STYLE_ARGUMENT = "bold magenta"
    click.rich_click.STYLE_USAGE_COMMAND = "bold green"
    click.rich_click.MAX_WIDTH = 110
except Exception:  # pragma: no cover - fallback path
    import click  # type: ignore

    HAS_RICH_CLICK = False

__all__ = ["click", "HAS_RICH_CLICK"]
