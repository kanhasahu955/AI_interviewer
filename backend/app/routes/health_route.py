"""Liveness + readiness + connection summary."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.core.connections import collect_connection_status

router = APIRouter()


@router.get("/health", tags=["health"])
def health() -> dict:
    return {
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "status": "ok",
    }


@router.get("/health/connections", tags=["health"])
def connections(probe_live: bool = False) -> dict:
    return collect_connection_status(probe_live=probe_live)
