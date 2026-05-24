"""Interview session record."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.core.types import PortableJSON
from app.models.base_model import TimestampMixin


class InterviewStatus(str, Enum):
    scheduled = "scheduled"
    live = "live"
    completed = "completed"
    cancelled = "cancelled"
    flagged = "flagged"


class Interview(TimestampMixin, table=True):
    __tablename__ = "interviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="users.id", index=True)
    jd_id: int = Field(foreign_key="job_descriptions.id", index=True)
    resume_id: int | None = Field(default=None, foreign_key="resumes.id")
    status: InterviewStatus = Field(default=InterviewStatus.scheduled, index=True)
    livekit_room: str | None = Field(default=None, max_length=255)
    duration_minutes: int = Field(default=30)
    notes: str | None = Field(default=None, max_length=2048)
    config: dict[str, Any] | None = Field(
        default=None, sa_column=Column(PortableJSON, nullable=True)
    )
    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    ended_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
