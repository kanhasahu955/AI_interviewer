"""Pydantic schemas for resume endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ResumePublic(BaseModel):
    id: int
    candidate_id: int
    file_name: str
    mime_type: str | None
    ingested: bool
    parsed: dict[str, Any] | None


class ResumeAnalyzeResponse(BaseModel):
    id: int
    file_name: str
    ingested: bool
    parsed: dict[str, Any]
    message: str
