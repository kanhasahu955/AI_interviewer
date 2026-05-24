"""Pydantic schemas for JD endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class JDCreate(BaseModel):
    title: str
    raw_text: str
    company: str | None = None
    seniority: str | None = None


class JDPublic(BaseModel):
    id: int
    recruiter_id: int
    title: str
    company: str | None
    seniority: str | None
    raw_text: str
    parsed_skills: dict[str, Any] | None
    ingested: bool
