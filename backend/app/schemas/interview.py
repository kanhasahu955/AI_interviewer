"""Pydantic schemas for interview endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.interview import InterviewStatus


class InterviewCreate(BaseModel):
    candidate_id: int
    jd_id: int
    resume_id: int | None = None
    duration_minutes: int = 30
    config: dict[str, Any] | None = None


class InterviewSelfCreate(BaseModel):
    resume_id: int | None = None
    duration_minutes: int = Field(default=30, ge=10, le=90)


class InterviewPublic(BaseModel):
    id: int
    candidate_id: int
    jd_id: int
    resume_id: int | None
    status: InterviewStatus
    livekit_room: str | None
    duration_minutes: int
    started_at: datetime | None
    ended_at: datetime | None


class LiveKitTokenResponse(BaseModel):
    url: str
    room: str
    identity: str
    token: str


class TurnPublic(BaseModel):
    idx: int
    skill_tag: str | None
    question: str
    answer_text: str | None
    score: dict[str, Any] | None
    started_at: datetime | None
    answered_at: datetime | None


class ProctorEventPublic(BaseModel):
    id: int
    interview_id: int
    kind: str
    severity: str
    ts: datetime
    payload: dict[str, Any] | None


class ProctorEventIngest(BaseModel):
    """Used by the browser to push events like tab-blur."""

    kind: str = Field(default="tab_blur")
    severity: str = Field(default="info")
    payload: dict[str, Any] | None = None


class ReportPublic(BaseModel):
    interview_id: int
    summary: str
    strengths: str | None
    weaknesses: str | None
    scores: dict[str, Any]
    recommendation: str
    overall_score: float
    generated_at: datetime
