"""Inline resume/JD ingest when Redis queue is unavailable."""

from __future__ import annotations

import logging

from sqlmodel import Session, select

from app.core.database import engine
from app.jobs.jd_ingest import ingest_jd_job
from app.jobs.resume_ingest import ingest_resume_job
from app.models.interview import Interview
from app.models.job_description import JobDescription
from app.models.resume import Resume

logger = logging.getLogger("app.services.interview_ingest")


def ingest_for_interview(interview: Interview, resume: Resume | None) -> None:
    """Embed resume + JD into Pinecone for the interview namespace."""
    if engine is None:
        logger.warning("ingest skipped: DB engine not initialised")
        return
    try:
        ingest_jd_job(interview.jd_id, interview.id)
        if resume is not None:
            ingest_resume_job(resume.id, interview.id)
    except Exception as exc:
        logger.warning("pinecone ingest failed (planner will use DB fallback): %s", exc)


def get_or_create_practice_jd(db: Session, candidate_id: int, resume: Resume) -> JobDescription:
    """Practice JD tailored to the candidate's resume skills."""
    title = "AI Practice Interview"
    existing = db.exec(
        select(JobDescription).where(
            JobDescription.recruiter_id == candidate_id,
            JobDescription.title == title,
        )
    ).first()
    if existing:
        return existing

    skills = (resume.parsed or {}).get("skills_detected") or []
    skill_line = ", ".join(skills[:15]) if skills else "general software engineering"
    raw_text = (
        f"Practice AI interview session for candidate {candidate_id}.\n"
        f"Focus on skills from their resume: {skill_line}.\n"
        "Ask behavioral and technical questions grounded in their projects and experience.\n"
        "Probe depth on listed technologies and past roles."
    )
    jd = JobDescription(
        recruiter_id=candidate_id,
        title=title,
        company="Interviewer AI",
        seniority="mid",
        raw_text=raw_text,
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd
