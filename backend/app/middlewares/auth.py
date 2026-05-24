"""JWT bearer auth + role-based authorization, surfaced to OpenAPI.

Using FastAPI's `HTTPBearer` makes Swagger UI render a lock icon on every
protected route and an "Authorize" dialog at the top of /docs. Paste your
`access_token` (from POST /auth/login) into that dialog once and Swagger
will send `Authorization: Bearer ...` on every subsequent call.
"""

from __future__ import annotations

from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

# `auto_error=False` lets us craft our own 401 messages and avoids a generic
# `Not authenticated` when the header is simply missing.
bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    scheme_name="BearerAuth",
    description=(
        "Paste the `access_token` returned by `POST /api/v1/auth/login` or "
        "`POST /api/v1/auth/signup`. Format: just the token, no `Bearer ` prefix."
    ),
    auto_error=False,
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub", 0) or 0)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*roles: UserRole):
    """Dependency factory: 403 unless `current_user.role` is in `roles`."""
    allowed: set[UserRole] = set(roles)

    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role; required one of {[r.value for r in allowed]}",
            )
        return user

    return _dep


require_candidate = require_roles(UserRole.candidate)
require_recruiter = require_roles(UserRole.recruiter, UserRole.admin)
require_admin = require_roles(UserRole.admin)
