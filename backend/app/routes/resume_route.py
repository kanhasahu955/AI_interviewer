"""Resume upload, analysis, and listing endpoints."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_db
from app.middlewares.auth import get_current_user
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.rag.loaders import load_document
from app.schemas.resume import ResumeAnalyzeResponse, ResumePublic
from app.services.resume_analysis_runner import run_analysis
from app.services.resume_analyzer import sanitize_resume_text
from app.streaming.resume_stream import create_resume_analysis_stream

logger = logging.getLogger("app.routes.resume")
router = APIRouter()


def _resume_dir() -> Path:
    path = settings.STORAGE_DIR / "resumes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _can_access_resume(user: User, resume: Resume) -> bool:
    if user.role == UserRole.admin:
        return True
    if resume.candidate_id == user.id:
        return True
    return user.role == UserRole.recruiter


def _apply_analysis(resume: Resume, db: Session) -> dict:
    result: dict | None = None
    for event in run_analysis(resume, db):
        if event.type == "result":
            result = event.detail.get("parsed") or {}
    return result or resume.parsed or {}


@router.post("", response_model=ResumePublic, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Resume:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name missing")

    safe_name = Path(file.filename).name
    target = _resume_dir() / f"u{user.id}-{safe_name}"
    content = await file.read()
    target.write_bytes(content)

    try:
        raw_text = sanitize_resume_text(load_document(target))
    except Exception:
        raw_text = None

    resume = Resume(
        candidate_id=user.id,
        file_name=safe_name,
        file_path=str(target),
        mime_type=file.content_type,
        raw_text=raw_text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("", response_model=list[ResumePublic])
def list_resumes(
    candidate_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Resume]:
    if candidate_id is not None:
        if user.role not in (UserRole.recruiter, UserRole.admin):
            raise HTTPException(status_code=403, detail="Not allowed")
        return list(
            db.exec(select(Resume).where(Resume.candidate_id == candidate_id))
        )
    return list(
        db.exec(select(Resume).where(Resume.candidate_id == user.id))
    )


@router.get("/{resume_id}", response_model=ResumePublic)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Resume:
    row = db.get(Resume, resume_id)
    if not row or not _can_access_resume(user, row):
        raise HTTPException(status_code=404, detail="Resume not found")
    return row


@router.post("/{resume_id}/analyze/stream")
def analyze_resume_stream(
    resume_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.get(Resume, resume_id)
    if not row or not _can_access_resume(user, row):
        raise HTTPException(status_code=404, detail="Resume not found")
    return create_resume_analysis_stream(row, db)


@router.post("/{resume_id}/analyze", response_model=ResumeAnalyzeResponse)
def analyze_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResumeAnalyzeResponse:
    row = db.get(Resume, resume_id)
    if not row or not _can_access_resume(user, row):
        raise HTTPException(status_code=404, detail="Resume not found")

    parsed = _apply_analysis(row, db)
    if not parsed.get("text_ready"):
        return ResumeAnalyzeResponse(
            id=row.id,
            file_name=row.file_name,
            ingested=row.ingested,
            parsed=parsed,
            message="File saved but text could not be extracted. Try PDF or DOCX.",
        )

    return ResumeAnalyzeResponse(
        id=row.id,
        file_name=row.file_name,
        ingested=row.ingested,
        parsed=parsed,
        message="Resume analyzed successfully.",
    )
