from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Iterable, Iterator, Sequence

from loguru import logger
import tqdm

from duprly.compat_click import click

try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.progress import Progress
    from rich.prompt import Confirm, IntPrompt, Prompt
    from rich.table import Table

    HAS_RICH = True
except Exception:  # pragma: no cover - fallback path
    HAS_RICH = False


class UI:
    def __init__(self, no_color: bool = False):
        self.no_color = no_color
        self.console = None
        if HAS_RICH:
            self.console = Console(color_system=None if no_color else "auto")

    def print(self, message: str = "", style: str | None = None) -> None:
        if HAS_RICH and self.console:
            self.console.print(message, style=style)
            return
        if style and not self.no_color:
            low = style.lower()
            if "red" in low:
                fg = "red"
            elif "yellow" in low:
                fg = "yellow"
            elif "green" in low:
                fg = "green"
            elif "magenta" in low:
                fg = "magenta"
            else:
                fg = "cyan"
            click.secho(message, fg=fg)
        else:
            click.echo(message)

    def print_json(self, data) -> None:
        if HAS_RICH and self.console:
            text = json.dumps(data, indent=2)
            self.console.print(text)
            return
        click.echo(json.dumps(data, indent=2))

    def panel(self, title: str, body: str, style: str = "cyan") -> None:
        if HAS_RICH and self.console:
            self.console.print(Panel.fit(body, title=title, border_style=style))
            return
        click.echo(f"\n== {title} ==\n{body}\n")

    def table(self, title: str, columns: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
        if HAS_RICH and self.console:
            table = Table(title=title, box=box.SIMPLE_HEAVY)
            for col in columns:
                table.add_column(col)
            for row in rows:
                table.add_row(*[str(v) for v in row])
            self.console.print(table)
            return

        click.echo(f"\n{title}")
        click.echo(" | ".join(columns))
        click.echo("-" * 80)
        for row in rows:
            click.echo(" | ".join(str(v) for v in row))

    @contextmanager
    def status(self, message: str) -> Iterator[None]:
        if HAS_RICH and self.console:
            with self.console.status(f"[bold cyan]{message}[/bold cyan]"):
                yield
            return
        click.echo(message)
        yield

    def track(self, iterable: Iterable, description: str) -> Iterable:
        if HAS_RICH and self.console:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=self.console,
                transient=True,
            )
            items = list(iterable)
            with progress:
                task_id = progress.add_task(description, total=len(items))
                for item in items:
                    yield item
                    progress.update(task_id, advance=1)
            return

        for item in tqdm.tqdm(iterable, desc=description):
            yield item

    def ask(self, prompt: str, default: str | None = None, choices: Sequence[str] | None = None) -> str:
        if HAS_RICH and self.console:
            return Prompt.ask(prompt, default=default, choices=choices)
        return click.prompt(prompt, default=default, type=click.Choice(choices) if choices else str)

    def ask_int(self, prompt: str, default: int | None = None) -> int:
        if HAS_RICH and self.console:
            return IntPrompt.ask(prompt, default=default)
        return click.prompt(prompt, default=default, type=int)

    def confirm(self, prompt: str, default: bool = True) -> bool:
        if HAS_RICH and self.console:
            return Confirm.ask(prompt, default=default)
        return click.confirm(prompt, default=default)


def print_exception(ui: UI, err: Exception) -> None:
    logger.debug("CLI error", exc_info=err)
    ui.print(f"Error: {err}", style="bold red")
