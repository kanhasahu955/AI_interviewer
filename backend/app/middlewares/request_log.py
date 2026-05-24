"""Request correlation-id + single-line access log.

Every incoming request gets an `X-Request-ID` (echoed back on the response and
attached to `request.state.request_id`). The middleware emits **one** structured
log line per request:

    POST /api/v1/auth/login  ->  200  (12ms)  req=8c3f...
    GET  /api/v1/users/me    ->  401  (1ms)   req=ab12...

On 5xx responses, the closing line includes the root error message when available.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.error_log import clear_last_error, last_error_summary

logger = logging.getLogger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"


def _short(rid: str) -> str:
    return rid.replace("-", "")[:8]


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Tags each request with a correlation id and logs status + duration."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming or str(uuid.uuid4())
        request.state.request_id = request_id
        clear_last_error()

        start = time.perf_counter()
        status_code = 500
        client = request.client.host if request.client else "?"
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"

        logger.info(
            "[dim cyan]→[/] [bold]%s[/] %s  [dim](from %s, req=%s)[/]",
            request.method,
            path,
            client,
            _short(request_id),
        )

        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            err_detail = last_error_summary.get()

            if status_code >= 500:
                level = logging.ERROR
            elif status_code >= 400:
                level = logging.WARNING
            else:
                level = logging.INFO

            colour = (
                "green"
                if status_code < 400
                else ("yellow" if status_code < 500 else "red bold")
            )

            if status_code >= 500 and err_detail:
                logger.log(
                    level,
                    "[%s]←[/] [bold]%s[/] %s  ->  [%s]%d[/]  (%dms)  req=%s\n"
                    "     [red]└─ %s[/]",
                    colour,
                    request.method,
                    request.url.path,
                    colour,
                    status_code,
                    int(elapsed_ms),
                    _short(request_id),
                    err_detail,
                )
            else:
                logger.log(
                    level,
                    "[%s]←[/] [bold]%s[/] %s  ->  [%s]%d[/]  (%dms)  req=%s",
                    colour,
                    request.method,
                    request.url.path,
                    colour,
                    status_code,
                    int(elapsed_ms),
                    _short(request_id),
                )

            clear_last_error()


def get_request_id(request: Request) -> str:
    """Helper for handlers that want the correlation id."""
    return getattr(request.state, "request_id", "-")
