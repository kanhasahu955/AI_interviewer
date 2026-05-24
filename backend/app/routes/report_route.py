"""Final interview report endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_db
from app.middlewares.auth import get_current_user
from app.models.interview import Interview
from app.models.job_description import JobDescription
from app.models.report import Report
from app.models.user import User, UserRole
from app.schemas.interview import ReportPublic

router = APIRouter()


@router.get("/{interview_id}", response_model=ReportPublic)
def get_report(
    interview_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportPublic:
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if user.role == UserRole.candidate and interview.candidate_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    if user.role == UserRole.recruiter:
        jd = db.get(JobDescription, interview.jd_id)
        if not jd or jd.recruiter_id != user.id:
            raise HTTPException(status_code=403, detail="Not allowed")

    row = db.exec(select(Report).where(Report.interview_id == interview_id)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not generated yet")

    return ReportPublic(
        interview_id=row.interview_id,
        summary=row.summary,
        strengths=row.strengths,
        weaknesses=row.weaknesses,
        scores=row.scores,
        recommendation=row.recommendation.value
        if hasattr(row.recommendation, "value")
        else str(row.recommendation),
        overall_score=row.overall_score,
        generated_at=row.generated_at,
    )
