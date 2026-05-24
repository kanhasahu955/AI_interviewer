"""User accounts (candidate / recruiter / admin)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

from app.models.base_model import TimestampMixin


class UserRole(str, Enum):
    candidate = "candidate"
    recruiter = "recruiter"
    admin = "admin"


class User(TimestampMixin, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    password_hash: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.candidate)
    is_active: bool = Field(default=True)

    # TOTP (authenticator app). Optional path; only used when OTP_MODE=totp.
    otp_secret: str | None = Field(default=None, max_length=64)
    otp_enabled: bool = Field(default=False)

    # Email OTP. We store only the hash so a DB leak can't replay codes.
    otp_code_hash: str | None = Field(default=None, max_length=255)
    otp_code_expires_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    otp_attempts: int = Field(default=0)
    email_verified: bool = Field(default=False)
