"""Job description records (created by recruiters)."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel

from app.core.types import PortableJSON
from app.models.base_model import TimestampMixin


class JobDescription(TimestampMixin, table=True):
    __tablename__ = "job_descriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    recruiter_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    company: str | None = Field(default=None, max_length=255)
    seniority: str | None = Field(default=None, max_length=64)
    raw_text: str = Field(sa_column=Column(Text, nullable=False))
    parsed_skills: dict[str, Any] | None = Field(
        default=None, sa_column=Column(PortableJSON, nullable=True)
    )
    ingested: bool = Field(default=False)
