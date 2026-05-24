"""User profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.database import get_db
from app.middlewares.auth import get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserPublic, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    if payload.full_name is not None:
        user.full_name = payload.full_name
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/candidates", response_model=list[UserPublic])
def search_candidates(
    q: str | None = Query(default=None, min_length=1, max_length=128),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
) -> list[User]:
    """Search active candidates by email or full name (recruiter / admin)."""
    stmt = select(User).where(
        User.role == UserRole.candidate,
        User.is_active == True,  # noqa: E712
    )
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(User.email.ilike(pattern), User.full_name.ilike(pattern))
        )
    stmt = stmt.order_by(User.full_name, User.email).limit(limit)
    return list(db.exec(stmt))
