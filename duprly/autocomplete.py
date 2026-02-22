from __future__ import annotations

import re
import sys
from typing import Callable

from duprly.ui import UI

try:
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import Completer, Completion

    HAS_PROMPT_TOOLKIT = True
except Exception:  # pragma: no cover - optional dependency
    HAS_PROMPT_TOOLKIT = False
    pt_prompt = None  # type: ignore[assignment]
    Completion = object  # type: ignore[assignment,misc]
    Completer = object  # type: ignore[assignment,misc]


_ID_RE = re.compile(r"\[(\d+)\]\s*$")


def parse_bracketed_id(text: str) -> str | None:
    match = _ID_RE.search(text.strip())
    if not match:
        return None
    return match.group(1)


def _item_label(entity: str, item: dict) -> str:
    if entity == "player":
        return f"{item.get('fullName', 'Unknown')} [{item.get('id', 'unknown')}]"
    return f"{item.get('clubName', 'Unknown')} [{item.get('clubId', 'unknown')}]"


def _item_id(entity: str, item: dict) -> str:
    if entity == "player":
        return str(item.get("id", ""))
    return str(item.get("clubId", ""))


def _choice_table_rows(entity: str, hits: list[dict]) -> list[list[object]]:
    rows: list[list[object]] = []
    for idx, item in enumerate(hits, start=1):
        if entity == "player":
            ratings = item.get("ratings", {}) or {}
            rows.append(
                [
                    idx,
                    item.get("fullName", "Unknown"),
                    item.get("id", "Unknown"),
                    item.get("shortAddress", ""),
                    ratings.get("singles", "NR"),
                    ratings.get("doubles", "NR"),
                ]
            )
        else:
            rows.append(
                [
                    idx,
                    item.get("clubName", "Unknown"),
                    item.get("clubId", "Unknown"),
                    item.get("shortAddress", ""),
                ]
            )
    return rows


def _prompt_numbered_selection(ui: UI, entity: str, hits: list[dict]) -> dict | None:
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]

    if entity == "player":
        ui.table(
            "Player Suggestions",
            ["#", "Name", "ID", "Location", "Singles", "Doubles"],
            _choice_table_rows(entity, hits),
        )
    else:
        ui.table(
            "Club Suggestions",
            ["#", "Name", "ID", "Location"],
            _choice_table_rows(entity, hits),
        )
    choice = ui.ask_int(f"Select {entity} number")
    if choice < 1 or choice > len(hits):
        return None
    return hits[choice - 1]


class CachedLookupCompleter(Completer):  # type: ignore[misc]
    def __init__(
        self,
        entity: str,
        limit: int,
        search_func: Callable[[str, int], list[dict]],
    ):
        self.entity = entity
        self.limit = limit
        self.search_func = search_func
        self.cache: dict[tuple[str, int], list[dict]] = {}
        self.last_hits: list[dict] = []
        self.last_error: str | None = None

    def _lookup(self, query: str) -> list[dict]:
        key = (query.strip().lower(), self.limit)
        if key in self.cache:
            return self.cache[key]
        try:
            hits = self.search_func(query, self.limit)
            self.last_error = None
        except Exception as err:  # pragma: no cover - interactive completion safety
            self.last_error = str(err)
            return []
        self.cache[key] = hits
        return hits

    def get_completions(self, document, complete_event):  # pragma: no cover - interactive only
        query = document.text.strip()
        if len(query) < 2:
            self.last_hits = []
            return
        hits = self._lookup(query)
        self.last_hits = hits
        for item in hits:
            label = _item_label(self.entity, item)
            yield Completion(label, start_position=-len(document.text))


def lookup_with_suggestions(
    ui: UI,
    entity: str,
    limit: int,
    search_func: Callable[[str, int], list[dict]],
    query: str | None = None,
) -> dict | None:
    is_tty = sys.stdin.isatty() and sys.stdout.isatty()
    if HAS_PROMPT_TOOLKIT and is_tty:
        completer = CachedLookupCompleter(entity=entity, limit=limit, search_func=search_func)
        prompt_label = f"Type {entity} name"
        user_text = pt_prompt(  # type: ignore[operator]
            f"{prompt_label}: ",
            completer=completer,
            complete_while_typing=True,
            default=query or "",
        )

        selected_id = parse_bracketed_id(user_text)
        selected: dict | None = None
        if selected_id:
            for item in completer.last_hits:
                if _item_id(entity, item) == selected_id:
                    selected = item
                    break
            if selected:
                return selected

        if len(completer.last_hits) == 1:
            return completer.last_hits[0]

        if len(completer.last_hits) > 1:
            return _prompt_numbered_selection(ui, entity, completer.last_hits)

        if completer.last_error:
            raise RuntimeError(completer.last_error)

        if user_text.strip():
            hits = search_func(user_text.strip(), limit)
            return _prompt_numbered_selection(ui, entity, hits)
        return None

    if not query:
        query = ui.ask(f"Enter {entity} name")
    hits = search_func(query, limit)
    return _prompt_numbered_selection(ui, entity, hits)
