"""Per-turn Q&A persistence for an interview session."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel

from app.core.types import PortableJSON
from app.models.base_model import TimestampMixin


class Turn(TimestampMixin, table=True):
    __tablename__ = "interview_turns"

    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(foreign_key="interviews.id", index=True)
    idx: int = Field(default=0, index=True)
    skill_tag: str | None = Field(default=None, max_length=128)
    question: str = Field(sa_column=Column(Text, nullable=False))
    answer_text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    answer_audio_url: str | None = Field(default=None, max_length=1024)
    score: dict[str, Any] | None = Field(
        default=None, sa_column=Column(PortableJSON, nullable=True)
    )
    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    answered_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
