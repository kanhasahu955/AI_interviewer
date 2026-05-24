"""Aggregate model imports so SQLModel metadata picks all tables."""

from app.models.base_model import TimestampMixin  # noqa: F401
from app.models.interview import Interview, InterviewStatus  # noqa: F401
from app.models.job_description import JobDescription  # noqa: F401
from app.models.proctoring_event import (  # noqa: F401
    ProctoringEvent,
    ProctoringKind,
    ProctoringSeverity,
)
from app.models.report import Recommendation, Report  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.turn import Turn  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401

__all__ = [
    "TimestampMixin",
    "User",
    "UserRole",
    "JobDescription",
    "Resume",
    "Interview",
    "InterviewStatus",
    "Turn",
    "ProctoringEvent",
    "ProctoringKind",
    "ProctoringSeverity",
    "Report",
    "Recommendation",
]
