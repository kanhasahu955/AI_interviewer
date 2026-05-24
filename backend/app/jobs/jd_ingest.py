"""Background job: embed a job description into Pinecone for an interview."""

from __future__ import annotations

import logging

from sqlmodel import Session

from app.core.database import engine
from app.models.job_description import JobDescription
from app.rag.ingest import ingest_jd_text

logger = logging.getLogger("app.jobs.jd_ingest")


def ingest_jd_job(jd_id: int, interview_id: int) -> dict:
    if engine is None:
        raise RuntimeError("DB engine not initialised")

    with Session(engine) as s:
        jd = s.get(JobDescription, jd_id)
        if jd is None:
            raise ValueError(f"JobDescription {jd_id} not found")

        count = ingest_jd_text(
            jd.raw_text, interview_id=interview_id, jd_id=jd.id
        )
        jd.ingested = True
        s.add(jd)
        s.commit()
        return {"jd_id": jd_id, "chunks": count}
