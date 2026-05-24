"""Pydantic schemas for user endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    role: UserRole
    is_active: bool
    otp_enabled: bool


class UserUpdate(BaseModel):
    full_name: str | None = None
