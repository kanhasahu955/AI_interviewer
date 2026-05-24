"""Bootstrap external observability (LangSmith env, Langfuse warmup)."""

from __future__ import annotations

import logging
import os

from app.core.config import settings

logger = logging.getLogger("app.observability")


def init_langsmith() -> None:
    """If LANGSMITH_TRACING is enabled, propagate creds to os.environ.

    LangChain reads LANGSMITH_* / LANGCHAIN_* env vars at module import time,
    so we surface the BaseSettings values back to the process env here.
    """
    if not settings.LANGSMITH_TRACING:
        return
    if not settings.LANGSMITH_API_KEY:
        logger.warning("LANGSMITH_TRACING is true but LANGSMITH_API_KEY is empty")
        return

    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", settings.LANGSMITH_API_KEY)
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGSMITH_API_KEY)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.LANGSMITH_PROJECT)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGSMITH_PROJECT)
    os.environ.setdefault("LANGSMITH_ENDPOINT", settings.LANGSMITH_ENDPOINT)
    os.environ.setdefault("LANGCHAIN_ENDPOINT", settings.LANGSMITH_ENDPOINT)
    logger.info("LangSmith tracing enabled (project=%s)", settings.LANGSMITH_PROJECT)


def init_langfuse() -> None:
    """Warm up the Langfuse callback handler to surface config errors early."""
    if not (settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY):
        return
    try:
        from app.langgraph.tracing import langfuse_handler

        if langfuse_handler() is not None:
            logger.info("Langfuse tracing enabled (host=%s)", settings.LANGFUSE_BASE_URL)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Langfuse init failed: %s", exc)


def init_all() -> None:
    init_langsmith()
    init_langfuse()
