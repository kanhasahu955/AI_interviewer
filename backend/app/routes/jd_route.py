"""Job description CRUD endpoints (recruiter-scoped)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_db
from app.middlewares.auth import get_current_user, require_roles
from app.models.job_description import JobDescription
from app.models.user import User, UserRole
from app.schemas.jd import JDCreate, JDPublic

router = APIRouter()


@router.post(
    "",
    response_model=JDPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_jd(
    payload: JDCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
) -> JobDescription:
    row = JobDescription(
        recruiter_id=user.id,
        title=payload.title,
        company=payload.company,
        seniority=payload.seniority,
        raw_text=payload.raw_text,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[JDPublic])
def list_jds(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[JobDescription]:
    if user.role == UserRole.admin:
        return list(db.exec(select(JobDescription)))
    return list(
        db.exec(select(JobDescription).where(JobDescription.recruiter_id == user.id))
    )


@router.get("/{jd_id}", response_model=JDPublic)
def get_jd(
    jd_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JobDescription:
    row = db.get(JobDescription, jd_id)
    if not row:
        raise HTTPException(status_code=404, detail="JD not found")
    if user.role == UserRole.candidate:
        raise HTTPException(status_code=403, detail="Not allowed")
    return row
