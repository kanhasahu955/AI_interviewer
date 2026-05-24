"""Interview lifecycle + LiveKit token endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_db
from app.helpers.api_error import AppError
from app.jobs.worker import enqueue
from app.livekit_agent.dispatch import (
    ensure_room,
    issue_candidate_token,
    room_name_for,
)
from app.middlewares.auth import get_current_user, require_roles
from app.models.interview import Interview, InterviewStatus
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.schemas.interview import (
    InterviewCreate,
    InterviewPublic,
    InterviewSelfCreate,
    LiveKitTokenResponse,
    TurnPublic,
)
from app.services.interview_ingest import get_or_create_practice_jd, ingest_for_interview
from app.services.interview_service import list_turns

logger = logging.getLogger("app.routes.interview")
router = APIRouter()


@router.post("", response_model=InterviewPublic, status_code=status.HTTP_201_CREATED)
def create_interview(
    payload: InterviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
) -> Interview:
    jd = db.get(JobDescription, payload.jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="JD not found")

    candidate = db.get(User, payload.candidate_id)
    if not candidate or candidate.role != UserRole.candidate:
        raise HTTPException(status_code=400, detail="Invalid candidate")

    resume = None
    if payload.resume_id is not None:
        resume = db.get(Resume, payload.resume_id)
        if not resume or resume.candidate_id != candidate.id:
            raise HTTPException(status_code=400, detail="Invalid resume")

    interview = Interview(
        candidate_id=candidate.id,
        jd_id=jd.id,
        resume_id=resume.id if resume else None,
        duration_minutes=payload.duration_minutes,
        config=payload.config,
        status=InterviewStatus.scheduled,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    interview.livekit_room = room_name_for(interview.id)
    db.add(interview)
    db.commit()
    db.refresh(interview)

    _enqueue_ingest(interview, resume)
    return interview


def _enqueue_ingest(interview: Interview, resume: Resume | None) -> None:
    if settings.USE_REDIS_QUEUE:
        try:
            enqueue("app.jobs.jd_ingest.ingest_jd_job", interview.jd_id, interview.id)
            if resume is not None:
                enqueue(
                    "app.jobs.resume_ingest.ingest_resume_job", resume.id, interview.id
                )
        except Exception as exc:
            logger.warning("could not enqueue ingest jobs: %s", exc)
            ingest_for_interview(interview, resume)
    else:
        ingest_for_interview(interview, resume)


@router.post(
    "/self",
    response_model=InterviewPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_self_interview(
    payload: InterviewSelfCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.candidate, UserRole.admin)),
) -> Interview:
    """Candidate starts an AI voice interview from their uploaded resume."""
    candidate_id = user.id if user.role == UserRole.candidate else user.id

    resume = None
    if payload.resume_id is not None:
        resume = db.get(Resume, payload.resume_id)
        if not resume or resume.candidate_id != candidate_id:
            raise HTTPException(status_code=400, detail="Invalid resume")
    else:
        rows = list(
            db.exec(select(Resume).where(Resume.candidate_id == candidate_id))
        )
        resume = max(rows, key=lambda r: r.id or 0) if rows else None

    if not resume:
        raise HTTPException(
            status_code=400,
            detail="Upload a resume before starting an AI interview",
        )

    jd = get_or_create_practice_jd(db, candidate_id, resume)

    interview = Interview(
        candidate_id=candidate_id,
        jd_id=jd.id,
        resume_id=resume.id,
        duration_minutes=payload.duration_minutes,
        config={"mode": "self_service"},
        status=InterviewStatus.scheduled,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    interview.livekit_room = room_name_for(interview.id)
    db.add(interview)
    db.commit()
    db.refresh(interview)

    _enqueue_ingest(interview, resume)
    try:
        await ensure_room(interview.id)
    except Exception as exc:
        logger.warning("ensure_room failed: %s", exc)
    return interview


@router.get("", response_model=list[InterviewPublic])
def list_interviews(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Interview]:
    stmt = select(Interview)
    if user.role == UserRole.candidate:
        stmt = stmt.where(Interview.candidate_id == user.id)
    elif user.role == UserRole.recruiter:
        stmt = stmt.join(JobDescription, JobDescription.id == Interview.jd_id).where(
            JobDescription.recruiter_id == user.id
        )
    return list(db.exec(stmt))


@router.get("/{interview_id}", response_model=InterviewPublic)
def get_interview_row(
    interview_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Interview:
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    _assert_can_see(user, interview, db)
    return interview


@router.post("/{interview_id}/token", response_model=LiveKitTokenResponse)
async def candidate_token(
    interview_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LiveKitTokenResponse:
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if user.role == UserRole.candidate and interview.candidate_id != user.id:
        raise HTTPException(status_code=403, detail="Not your interview")

    try:
        await ensure_room(interview_id)
        payload = issue_candidate_token(
            interview_id,
            identity=f"candidate-{interview.candidate_id}",
            name=user.full_name or user.email,
        )
    except RuntimeError as exc:
        raise AppError(str(exc), status_code=503) from exc

    return LiveKitTokenResponse(**payload)


@router.post("/{interview_id}/end", response_model=InterviewPublic)
def end_interview_route(
    interview_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Interview:
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    _assert_can_see(user, interview, db)

    from datetime import datetime, timezone

    interview.status = InterviewStatus.completed
    interview.ended_at = datetime.now(timezone.utc)
    db.add(interview)
    db.commit()
    db.refresh(interview)

    if settings.USE_REDIS_QUEUE:
        try:
            enqueue("app.jobs.report_generate.generate_report_job", interview.id)
        except Exception as exc:
            logger.warning("could not enqueue report job: %s", exc)

    return interview


@router.get("/{interview_id}/turns", response_model=list[TurnPublic])
def get_turns(
    interview_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TurnPublic]:
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    _assert_can_see(user, interview, db)
    rows = list_turns(interview_id)
    return [
        TurnPublic(
            idx=t.idx,
            skill_tag=t.skill_tag,
            question=t.question,
            answer_text=t.answer_text,
            score=t.score,
            started_at=t.started_at,
            answered_at=t.answered_at,
        )
        for t in rows
    ]


def _assert_can_see(user: User, interview: Interview, db: Session) -> None:
    if user.role == UserRole.admin:
        return
    if user.role == UserRole.candidate and interview.candidate_id == user.id:
        return
    if user.role == UserRole.recruiter:
        jd = db.get(JobDescription, interview.jd_id)
        if jd and jd.recruiter_id == user.id:
            return
    raise HTTPException(status_code=403, detail="Not allowed")
