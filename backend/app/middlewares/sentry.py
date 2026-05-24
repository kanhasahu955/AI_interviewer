"""Sentry initialisation (no-op when SENTRY_DSN is unset)."""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger("app.middlewares.sentry")


def init_sentry() -> None:
    if not settings.SENTRY_DSN:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.APP_ENV,
            traces_sample_rate=0.1,
            integrations=[StarletteIntegration(), FastApiIntegration()],
        )
        logger.info("Sentry initialised (env=%s)", settings.APP_ENV)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sentry init failed: %s", exc)
