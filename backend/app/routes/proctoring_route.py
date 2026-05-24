"""Proctoring event ingestion + read endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_db
from app.middlewares.auth import get_current_user
from app.models.interview import Interview
from app.models.proctoring_event import ProctoringKind, ProctoringSeverity
from app.models.user import User, UserRole
from app.schemas.interview import ProctorEventIngest, ProctorEventPublic
from app.services.interview_service import (
    list_proctor_events,
    record_proctor_event,
)

router = APIRouter()


def _assert_can_touch(user: User, interview: Interview, db: Session) -> None:
    if user.role == UserRole.admin:
        return
    if user.role == UserRole.candidate and interview.candidate_id == user.id:
        return
    if user.role == UserRole.recruiter:
        from app.models.job_description import JobDescription

        jd = db.get(JobDescription, interview.jd_id)
        if jd and jd.recruiter_id == user.id:
            return
    raise HTTPException(status_code=403, detail="Not allowed")


@router.post("/{interview_id}/events", response_model=ProctorEventPublic)
def ingest_event(
    interview_id: int,
    payload: ProctorEventIngest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProctorEventPublic:
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    _assert_can_touch(user, interview, db)

    try:
        kind = ProctoringKind(payload.kind)
    except ValueError:
        kind = ProctoringKind.custom
    try:
        severity = ProctoringSeverity(payload.severity)
    except ValueError:
        severity = ProctoringSeverity.info

    evt = record_proctor_event(
        interview_id, kind=kind, severity=severity, payload=payload.payload
    )
    return ProctorEventPublic(
        id=evt.id,
        interview_id=evt.interview_id,
        kind=evt.kind.value if hasattr(evt.kind, "value") else str(evt.kind),
        severity=evt.severity.value
        if hasattr(evt.severity, "value")
        else str(evt.severity),
        ts=evt.ts,
        payload=evt.payload,
    )


@router.get("/{interview_id}/events", response_model=list[ProctorEventPublic])
def list_events(
    interview_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProctorEventPublic]:
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    _assert_can_touch(user, interview, db)

    rows = list_proctor_events(interview_id)
    return [
        ProctorEventPublic(
            id=r.id,
            interview_id=r.interview_id,
            kind=r.kind.value if hasattr(r.kind, "value") else str(r.kind),
            severity=r.severity.value
            if hasattr(r.severity, "value")
            else str(r.severity),
            ts=r.ts,
            payload=r.payload,
        )
        for r in rows
    ]
