"""Application-specific errors mapped to HTTP responses.

These are *expected* failure modes (`raise NotFoundError("user 42")`) and are
serialised by the global handler in `main.py` to a consistent JSON shape:

    {
      "error": {
        "code":       "NOT_FOUND",
        "message":    "user 42",
        "request_id": "8c3f...",
        "details":    null
      }
    }

Catch-all `Exception` → 500 uses the same shape with `code="INTERNAL_ERROR"`.
Validation errors (Pydantic) → 422 use `code="VALIDATION_ERROR"` and put the
field-level breakdown into `details`.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for domain failures with an HTTP-friendly payload."""

    status_code: int = 400
    code: str = "BAD_REQUEST"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: Any | None = None,
    ) -> None:
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class BadRequestError(AppError):
    status_code = 400
    code = "BAD_REQUEST"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"

    def __init__(self, message: str = "Resource not found", **kw: Any) -> None:
        super().__init__(message, **kw)


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class UnprocessableError(AppError):
    status_code = 422
    code = "UNPROCESSABLE_ENTITY"


class RateLimitError(AppError):
    status_code = 429
    code = "RATE_LIMITED"


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "SERVICE_UNAVAILABLE"


class UpstreamError(AppError):
    """Third-party service (LLM, LiveKit, Pinecone, etc.) failed."""

    status_code = 502
    code = "UPSTREAM_ERROR"
