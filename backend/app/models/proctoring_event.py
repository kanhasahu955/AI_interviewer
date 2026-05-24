"""Proctoring events emitted during an interview session."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.core.types import PortableJSON
from app.models.base_model import TimestampMixin


class ProctoringKind(str, Enum):
    face_missing = "face_missing"
    multi_face = "multi_face"
    identity_mismatch = "identity_mismatch"
    gaze_away = "gaze_away"
    speaker_mismatch = "speaker_mismatch"
    silence = "silence"
    tab_blur = "tab_blur"
    network_drop = "network_drop"
    custom = "custom"


class ProctoringSeverity(str, Enum):
    info = "info"
    warn = "warn"
    critical = "critical"


class ProctoringEvent(TimestampMixin, table=True):
    __tablename__ = "proctoring_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(foreign_key="interviews.id", index=True)
    kind: ProctoringKind = Field(index=True)
    severity: ProctoringSeverity = Field(default=ProctoringSeverity.info)
    ts: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    payload: dict[str, Any] | None = Field(
        default=None, sa_column=Column(PortableJSON, nullable=True)
    )
