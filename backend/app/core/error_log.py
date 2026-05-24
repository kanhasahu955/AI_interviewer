"""Prominent, readable server error output for the terminal."""

from __future__ import annotations

import contextvars
import logging
import re
from typing import Any

from rich.panel import Panel
from rich.text import Text

from app.core.config import settings
from app.core.logging_config import get_console

logger = logging.getLogger("app.error")

# Set by exception handlers; read by request log for the closing line.
last_error_summary: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "last_error_summary",
    default=None,
)


def extract_root_message(exc: BaseException) -> str:
    """Pull the shortest useful message from wrapped DB/driver errors."""
    seen: set[int] = set()
    current: BaseException | None = exc
    messages: list[str] = []

    while current is not None and id(current) not in seen:
        seen.add(id(current))
        text = str(current).strip()
        if text and text not in messages:
            messages.append(text)
        current = current.__cause__ or current.__context__

    if not messages:
        return type(exc).__name__

    # Prefer the innermost driver message (often clearest for Snowflake).
    for candidate in reversed(messages):
        cleaned = _clean_message(candidate)
        if cleaned:
            return cleaned

    return _clean_message(messages[0]) or type(exc).__name__


def _clean_message(raw: str) -> str:
    """Collapse whitespace and drop sqlalchemy wrapper noise when possible."""
    text = re.sub(r"\s+", " ", raw).strip()
    # Snowflake: "002023 (22000): SQL compilation error: ..."
    m = re.search(
        r"(SQL compilation error:.*?)(?:\[SQL:|$)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    m = re.search(r"ProgrammingError:\s*(.+?)(?:\s*\[SQL:|$)", text)
    if m:
        return m.group(1).strip()
    if len(text) > 280:
        return text[:277] + "…"
    return text


def log_request_error(
    *,
    code: str,
    method: str,
    path: str,
    request_id: str,
    exc: BaseException,
    details: Any | None = None,
) -> str:
    """Emit a large, scannable error block and return the root message."""
    root = extract_root_message(exc)
    last_error_summary.set(root)

    console = get_console()
    body = Text()
    body.append("Request   ", style="bold dim")
    body.append(f"{method} {path}\n", style="bold white")
    body.append("Request ID", style="bold dim")
    body.append(f"  {request_id}\n", style="cyan")
    body.append("Error code", style="bold dim")
    body.append(f"  {code}\n", style="yellow")
    body.append("Message   ", style="bold dim")
    body.append(f"{root}\n", style="bold red")
    if details is not None:
        body.append("Details   ", style="bold dim")
        body.append(f"{details}\n", style="white")

    console.print()
    console.print(
        Panel(
            body,
            title=f"[bold red on default]  ✖  {code}  [/]",
            border_style="bright_red",
            padding=(1, 2),
            expand=True,
        )
    )

    if settings.APP_DEBUG:
        console.print("[dim]Full traceback:[/]")
        console.print_exception(show_locals=False, max_frames=12)
    else:
        logger.error(
            "[bold red]%s[/] %s %s · req=%s · %s",
            code,
            method,
            path,
            request_id[:8],
            root,
        )

    console.print()
    return root


def clear_last_error() -> None:
    last_error_summary.set(None)
