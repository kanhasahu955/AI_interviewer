"""Global FastAPI exception handlers.

Centralises *every* error path to one place so:
  - Clients always receive the same JSON envelope.
  - Terminal output shows a large, readable error panel for 5xx failures.
  - Full tracebacks only when APP_DEBUG=true.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_log import clear_last_error, extract_root_message, log_request_error
from app.helpers.api_error import AppError
from app.middlewares.request_log import REQUEST_ID_HEADER, get_request_id

logger = logging.getLogger("app.error")


def _envelope(
    *,
    code: str,
    message: str,
    request_id: str,
    details: Any | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return body


def _json(
    status_code: int,
    payload: dict[str, Any],
    request_id: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers={REQUEST_ID_HEADER: request_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire all handlers onto the FastAPI app."""

    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        rid = get_request_id(request)
        if exc.status_code >= 500:
            msg = log_request_error(
                code=exc.code,
                method=request.method,
                path=request.url.path,
                request_id=rid,
                exc=exc,
                details=exc.details,
            )
        else:
            clear_last_error()
            logger.warning(
                "[yellow]%s[/] %s  ·  req=%s  ·  %s",
                exc.code,
                exc.message,
                rid[:8],
                request.url.path,
            )
            msg = exc.message
        return _json(
            exc.status_code,
            _envelope(
                code=exc.code,
                message=msg if exc.status_code >= 500 else exc.message,
                request_id=rid,
                details=exc.details,
            ),
            rid,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        rid = get_request_id(request)
        code = _http_code_name(exc.status_code)
        clear_last_error()
        logger.warning(
            "[yellow]%s[/] %s  ·  req=%s  ·  %s",
            code,
            exc.detail,
            rid[:8],
            request.url.path,
        )
        return _json(
            exc.status_code,
            _envelope(code=code, message=str(exc.detail), request_id=rid),
            rid,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        rid = get_request_id(request)
        details = _format_validation(exc.errors())
        summary = "; ".join(d["message"] for d in details[:3])
        clear_last_error()
        logger.warning(
            "[yellow]VALIDATION_ERROR[/] %s  ·  req=%s  ·  %s",
            summary,
            rid[:8],
            request.url.path,
        )
        return _json(
            422,
            _envelope(
                code="VALIDATION_ERROR",
                message="Request payload failed validation",
                request_id=rid,
                details=details,
            ),
            rid,
        )

    @app.exception_handler(IntegrityError)
    async def _integrity(request: Request, exc: IntegrityError) -> JSONResponse:
        rid = get_request_id(request)
        msg = _summarise_integrity(exc)
        clear_last_error()
        logger.warning(
            "[yellow]CONFLICT[/] %s  ·  req=%s  ·  %s",
            msg,
            rid[:8],
            request.url.path,
        )
        return _json(
            409,
            _envelope(code="CONFLICT", message=msg, request_id=rid),
            rid,
        )

    @app.exception_handler(OperationalError)
    async def _db_down(
        request: Request, exc: OperationalError
    ) -> JSONResponse:
        rid = get_request_id(request)
        msg = log_request_error(
            code="DB_UNAVAILABLE",
            method=request.method,
            path=request.url.path,
            request_id=rid,
            exc=exc,
        )
        return _json(
            503,
            _envelope(
                code="DB_UNAVAILABLE",
                message=msg,
                request_id=rid,
            ),
            rid,
        )

    @app.exception_handler(SQLAlchemyError)
    async def _sqla(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        rid = get_request_id(request)
        msg = log_request_error(
            code="DB_ERROR",
            method=request.method,
            path=request.url.path,
            request_id=rid,
            exc=exc,
        )
        return _json(
            500,
            _envelope(
                code="DB_ERROR",
                message=msg,
                request_id=rid,
            ),
            rid,
        )

    @app.exception_handler(Exception)
    async def _catch_all(request: Request, exc: Exception) -> JSONResponse:
        rid = get_request_id(request)
        msg = log_request_error(
            code="INTERNAL_ERROR",
            method=request.method,
            path=request.url.path,
            request_id=rid,
            exc=exc,
        )
        return _json(
            500,
            _envelope(
                code="INTERNAL_ERROR",
                message=msg,
                request_id=rid,
            ),
            rid,
        )


_HTTP_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    410: "GONE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "UNPROCESSABLE_ENTITY",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}


def _http_code_name(status_code: int) -> str:
    return _HTTP_CODES.get(status_code, f"HTTP_{status_code}")


def _format_validation(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []) if x not in ("body",))
        msg = err.get("msg", "invalid")
        out.append(
            {
                "field": loc or "(root)",
                "message": f"{loc or '(root)'}: {msg}" if loc else msg,
                "type": err.get("type", "value_error"),
            }
        )
    return out


def _summarise_integrity(exc: IntegrityError) -> str:
    raw = extract_root_message(exc)
    lower = raw.lower()
    if "duplicate" in lower or "unique" in lower:
        return "A record with the same unique value already exists."
    if "foreign key" in lower:
        return "Referenced record does not exist."
    if "not null" in lower or "cannot be null" in lower:
        return "A required field is missing."
    return "Database constraint violated."
