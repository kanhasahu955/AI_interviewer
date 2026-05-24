"""Final interview report (generated post-session)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel

from app.core.types import PortableJSON
from app.models.base_model import TimestampMixin


class Recommendation(str, Enum):
    strong_hire = "strong_hire"
    hire = "hire"
    borderline = "borderline"
    no_hire = "no_hire"


class Report(TimestampMixin, table=True):
    __tablename__ = "interview_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(foreign_key="interviews.id", unique=True, index=True)
    summary: str = Field(sa_column=Column(Text, nullable=False))
    strengths: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    weaknesses: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    scores: dict[str, Any] = Field(sa_column=Column(PortableJSON, nullable=False))
    recommendation: Recommendation = Field(default=Recommendation.borderline)
    overall_score: float = Field(default=0.0)
    generated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
