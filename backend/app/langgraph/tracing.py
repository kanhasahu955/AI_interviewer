"""Langfuse tracing helpers for LangGraph runs."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from app.core.config import settings

logger = logging.getLogger("app.langgraph.tracing")


@lru_cache(maxsize=1)
def langfuse_handler() -> Any | None:
    """Return a Langfuse LangChain callback handler if configured.

    Langfuse v3 reads creds from env (`LANGFUSE_PUBLIC_KEY`,
    `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`); we surface our Settings values to
    `os.environ` so the SDK picks them up at import time.
    """
    import os

    if not (settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY):
        return None

    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.LANGFUSE_PUBLIC_KEY)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.LANGFUSE_SECRET_KEY)
    os.environ.setdefault(
        "LANGFUSE_HOST", settings.LANGFUSE_BASE_URL or settings.LANGFUSE_HOST
    )

    try:
        from langfuse.langchain import CallbackHandler

        return CallbackHandler()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Langfuse handler unavailable: %s", exc)
        return None


def callbacks() -> list[Any]:
    handlers: list[Any] = []
    h = langfuse_handler()
    if h is not None:
        handlers.append(h)
    return handlers


def run_config(*, interview_id: int | None = None, tags: list[str] | None = None) -> dict:
    cfg: dict[str, Any] = {"callbacks": callbacks()}
    metadata: dict[str, Any] = {}
    if interview_id is not None:
        metadata["interview_id"] = interview_id
    if metadata:
        cfg["metadata"] = metadata
    if tags:
        cfg["tags"] = tags
    return cfg
