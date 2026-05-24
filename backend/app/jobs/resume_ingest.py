"""Background job: parse + chunk + embed a resume into Pinecone."""

from __future__ import annotations

import logging

from sqlmodel import Session

from app.core.database import engine
from app.models.resume import Resume
from app.rag.ingest import ingest_resume_file, ingest_resume_text
from app.rag.loaders import load_document

logger = logging.getLogger("app.jobs.resume_ingest")


def ingest_resume_job(resume_id: int, interview_id: int) -> dict:
    if engine is None:
        raise RuntimeError("DB engine not initialised")

    with Session(engine) as s:
        resume = s.get(Resume, resume_id)
        if resume is None:
            raise ValueError(f"Resume {resume_id} not found")

        if resume.raw_text:
            count = ingest_resume_text(
                resume.raw_text,
                interview_id=interview_id,
                candidate_id=resume.candidate_id,
            )
        else:
            text = load_document(resume.file_path)
            resume.raw_text = text
            count = ingest_resume_file(
                resume.file_path,
                interview_id=interview_id,
                candidate_id=resume.candidate_id,
            )

        resume.ingested = True
        s.add(resume)
        s.commit()
        return {"resume_id": resume_id, "chunks": count}
