"""Probe configured external services and log a connection summary."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.core.logging_config import print_connection_banner

logger = logging.getLogger("app.connections")


def _check_database(probe_live: bool) -> dict:
    name = f"db_{settings.DB_PROVIDER.value}"
    try:
        from sqlalchemy import text

        from app.core.database import db_startup_error, engine

        if engine is None:
            return {
                "name": name,
                "status": "error",
                "connected": False,
                "message": db_startup_error or "engine not initialised",
            }

        if not probe_live:
            return {
                "name": name,
                "status": "ok",
                "connected": True,
                "message": "engine ready",
            }

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "name": name,
            "status": "ok",
            "connected": True,
            "message": "reachable",
        }
    except Exception as exc:
        return {
            "name": name,
            "status": "error",
            "connected": False,
            "message": str(exc).splitlines()[0][:160],
        }


def _check_redis(probe_live: bool) -> dict:
    try:
        from app.core.redis_client import ping_redis

        if not probe_live:
            return {
                "name": "redis",
                "status": "ok",
                "connected": True,
                "message": settings.REDIS_URL,
            }
        ping_redis()
        return {
            "name": "redis",
            "status": "ok",
            "connected": True,
            "message": settings.REDIS_URL,
        }
    except Exception as exc:
        return {
            "name": "redis",
            "status": "error",
            "connected": False,
            "message": str(exc)[:160],
        }


def _check_pinecone(probe_live: bool) -> dict:
    if not settings.PINECONE_API_KEY:
        return {
            "name": "pinecone",
            "status": "disabled",
            "connected": False,
            "message": "PINECONE_API_KEY not set",
        }
    try:
        if not probe_live:
            return {
                "name": "pinecone",
                "status": "ok",
                "connected": True,
                "message": settings.PINECONE_INDEX_NAME,
            }
        from app.rag.pinecone_store import PineconeStore

        store = PineconeStore()
        store._get_client().list_indexes()
        return {
            "name": "pinecone",
            "status": "ok",
            "connected": True,
            "message": f"index={settings.PINECONE_INDEX_NAME}",
        }
    except Exception as exc:
        return {
            "name": "pinecone",
            "status": "error",
            "connected": False,
            "message": str(exc)[:160],
        }


def _check_keys() -> list[dict]:
    keys = [
        ("openai", settings.OPENAI_API_KEY),
        ("groq", settings.GROQ_API_KEY),
        ("anthropic", settings.ANTHROPIC_API_KEY),
        ("google", settings.GOOGLE_API_KEY),
        ("langfuse", settings.LANGFUSE_SECRET_KEY),
    ]
    results = []
    for name, value in keys:
        configured = bool(value)
        results.append(
            {
                "name": name,
                "status": "ok" if configured else "disabled",
                "connected": configured,
                "message": "key set" if configured else "not configured",
            }
        )
    return results


def _check_livekit() -> dict:
    configured = bool(
        settings.LIVEKIT_URL
        and settings.LIVEKIT_API_KEY
        and settings.LIVEKIT_API_SECRET
    )
    return {
        "name": "livekit",
        "status": "ok" if configured else "disabled",
        "connected": configured,
        "message": settings.LIVEKIT_URL or "not configured",
    }


def collect_connection_status(probe_live: bool = False) -> dict:
    connections: list[dict] = []
    connections.append(_check_database(probe_live))
    connections.append(_check_redis(probe_live))
    connections.append(_check_pinecone(probe_live))
    connections.append(_check_livekit())
    connections.extend(_check_keys())

    statuses = {c["status"] for c in connections}
    if "error" in statuses:
        overall = "degraded"
    elif statuses <= {"disabled"}:
        overall = "disabled"
    else:
        overall = "ok"

    return {
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "status": overall,
        "connections": connections,
    }


def log_connection_status(probe_live: bool = False) -> dict:
    summary = collect_connection_status(probe_live=probe_live)
    try:
        print_connection_banner(summary)
    except Exception as exc:
        logger.warning("Could not render connection banner: %s", exc)
    return summary
