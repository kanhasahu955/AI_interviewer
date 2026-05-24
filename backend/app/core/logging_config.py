"""Structured logging + startup banners for Interviewer AI."""

import logging

from rich import box
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.core.config import settings

_console = Console(force_terminal=True, soft_wrap=False, width=None)


def get_console() -> Console:
    return _console

_STATUS_STYLE = {
    "ok": ("green", "✔"),
    "error": ("red", "✖"),
    "degraded": ("yellow", "⚠"),
    "disabled": ("dim", "○"),
    "unknown": ("blue", "?"),
}

_OVERALL_BORDER = {
    "ok": "green",
    "degraded": "yellow",
    "disabled": "dim",
    "error": "red",
}

_QUIET_LOGGERS = (
    "httpx",
    "httpcore",
    "urllib3",
    "pinecone",
    "openai",
    "openai._base_client",
    "botocore",
    "boto3",
    "snowflake",
    "snowflake.connector",
    "watchfiles",
    "asyncio",
    "charset_normalizer",
    "filelock",
    "passlib",
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "sqlalchemy.dialects",
    "sqlalchemy.orm",
    "multipart",
    "python_multipart",
    "matplotlib",
    "PIL",
)


def setup_logging() -> None:
    handler = RichHandler(
        console=_console,
        rich_tracebacks=True,
        tracebacks_show_locals=settings.APP_DEBUG,
        tracebacks_width=120,
        tracebacks_extra_lines=2,
        tracebacks_suppress=[
            "snowflake.connector",
            "sqlalchemy.engine",
            "sqlalchemy.orm",
            "starlette.middleware",
        ],
        markup=True,
        show_time=True,
        show_path=settings.APP_DEBUG,
        log_time_format="[%H:%M:%S]",
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[handler],
        force=True,
    )

    app_level = logging.DEBUG if settings.APP_DEBUG else logging.INFO
    logging.getLogger("app").setLevel(app_level)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def _status_cell(status: str) -> Text:
    color, icon = _STATUS_STYLE.get(status, ("white", "•"))
    return Text(f"{icon} {status.upper()}", style=color)


def print_startup_banner() -> None:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", justify="right")
    grid.add_column(style="white")

    grid.add_row("App", settings.APP_NAME)
    grid.add_row("Env", settings.APP_ENV)
    grid.add_row("Database", settings.DB_PROVIDER.value)
    grid.add_row("LLM", f"Groq · {settings.GROQ_MODEL}")
    grid.add_row("Vector DB", settings.PINECONE_INDEX_NAME)
    grid.add_row("LiveKit", settings.LIVEKIT_URL or "(not configured)")

    _console.print()
    _console.print(
        Panel(
            grid,
            title="[bold white]Interviewer AI[/bold white]",
            subtitle="[dim]starting…[/dim]",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def print_connection_banner(summary: dict) -> None:
    overall = summary.get("status", "unknown")
    border = _OVERALL_BORDER.get(overall, "blue")

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        expand=True,
        padding=(0, 1),
    )
    table.add_column("Service", style="bold white", no_wrap=True)
    table.add_column("Status", justify="center", no_wrap=True)
    table.add_column("Live", justify="center", no_wrap=True)
    table.add_column("Message", ratio=2)

    for conn in summary.get("connections", []):
        connected = conn.get("connected", False)
        live = Text("yes", style="green") if connected else Text("no", style="red")
        if conn.get("status") == "disabled":
            live = Text("—", style="dim")

        table.add_row(
            conn["name"].replace("_", " ").title(),
            _status_cell(conn.get("status", "unknown")),
            live,
            conn.get("message", ""),
        )

    title = Text()
    title.append(summary.get("app", "App"), style="bold white")
    title.append("  ·  ", style="dim")
    title.append("connections ", style="dim")
    title.append(overall.upper(), style=_OVERALL_BORDER.get(overall, "white"))

    _console.print()
    _console.print(Panel(table, title=title, border_style=border, padding=(1, 2)))
    _console.print()
