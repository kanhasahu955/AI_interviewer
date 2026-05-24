"""Candidate resume records."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel

from app.core.types import PortableJSON
from app.models.base_model import TimestampMixin


class Resume(TimestampMixin, table=True):
    __tablename__ = "resumes"

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="users.id", index=True)
    file_name: str = Field(max_length=512)
    file_path: str = Field(max_length=1024)
    mime_type: str | None = Field(default=None, max_length=128)
    raw_text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    parsed: dict[str, Any] | None = Field(
        default=None, sa_column=Column(PortableJSON, nullable=True)
    )
    ingested: bool = Field(default=False)
