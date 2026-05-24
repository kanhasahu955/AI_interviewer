"""Step-by-step resume analysis with observable progress events."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Iterator

from sqlmodel import Session

from app.models.resume import Resume
from app.rag.loaders import load_document
from app.services.resume_analyzer import analyze_resume_text, sanitize_resume_text


@dataclass
class AnalysisEvent:
    type: str  # stage | log | progress | result | error
    step: str = ""
    message: str = ""
    progress: int = 0
    status: str = "running"  # pending | running | done | error
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _suffix_label(path: str | None) -> str:
    if not path:
        return "document"
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return "PDF"
    if suffix in {".docx", ".doc"}:
        return "Word document"
    if suffix in {".txt", ".md"}:
        return "text file"
    return suffix.lstrip(".") or "document"


def run_analysis(resume: Resume, db: Session) -> Iterator[AnalysisEvent]:
    """Run analysis synchronously, yielding progress events after each step."""
    yield AnalysisEvent(
        type="stage",
        step="started",
        message="Starting resume analysis",
        progress=5,
        status="running",
        detail={"resume_id": resume.id, "file_name": resume.file_name},
    )

    yield AnalysisEvent(
        type="log",
        step="started",
        message=f"Analyzing {resume.file_name}",
        progress=8,
        status="done",
    )

    if not resume.raw_text and resume.file_path:
        label = _suffix_label(resume.file_path)
        yield AnalysisEvent(
            type="stage",
            step="load_document",
            message=f"Reading {label} from storage",
            progress=15,
            status="running",
            detail={"file_path": Path(resume.file_path).name},
        )
        try:
            raw = load_document(resume.file_path)
            resume.raw_text = sanitize_resume_text(raw)
            yield AnalysisEvent(
                type="log",
                step="load_document",
                message=f"Extracted {len(resume.raw_text):,} characters from {label}",
                progress=30,
                status="done",
                detail={"char_count": len(resume.raw_text or "")},
            )
        except Exception as exc:
            yield AnalysisEvent(
                type="error",
                step="load_document",
                message=f"Could not read file: {exc}",
                progress=30,
                status="error",
            )
            resume.raw_text = None
    elif resume.raw_text:
        yield AnalysisEvent(
            type="stage",
            step="sanitize",
            message="Normalizing stored resume text",
            progress=20,
            status="running",
        )
        before = len(resume.raw_text)
        resume.raw_text = sanitize_resume_text(resume.raw_text)
        yield AnalysisEvent(
            type="log",
            step="sanitize",
            message=f"Cleaned text ({before:,} → {len(resume.raw_text):,} chars)",
            progress=35,
            status="done",
        )
    else:
        yield AnalysisEvent(
            type="log",
            step="load_document",
            message="No text available — file may be unreadable",
            progress=30,
            status="error",
        )

    yield AnalysisEvent(
        type="stage",
        step="extract_skills",
        message="Scanning for skills and keywords",
        progress=45,
        status="running",
    )

    parsed = analyze_resume_text(resume.raw_text)

    skills = parsed.get("skills_detected") or []
    yield AnalysisEvent(
        type="log",
        step="extract_skills",
        message=f"Found {len(skills)} skill match(es)",
        progress=60,
        status="done",
        detail={"skills_detected": skills[:10]},
    )

    yield AnalysisEvent(
        type="stage",
        step="extract_sections",
        message="Detecting resume sections",
        progress=70,
        status="running",
    )
    sections = parsed.get("sections_found") or []
    yield AnalysisEvent(
        type="log",
        step="extract_sections",
        message=f"Sections: {', '.join(sections) if sections else 'none detected'}",
        progress=78,
        status="done",
        detail={"sections_found": sections},
    )

    yield AnalysisEvent(
        type="stage",
        step="extract_contact",
        message="Extracting contact hints",
        progress=82,
        status="running",
    )
    emails = parsed.get("emails") or []
    phones = parsed.get("phones") or []
    yield AnalysisEvent(
        type="log",
        step="extract_contact",
        message=f"Emails: {len(emails)} · Phones: {len(phones)}",
        progress=88,
        status="done",
        detail={"emails": emails, "phones": phones},
    )

    yield AnalysisEvent(
        type="stage",
        step="save",
        message="Saving analysis to database",
        progress=92,
        status="running",
    )
    resume.parsed = parsed
    db.add(resume)
    db.commit()
    db.refresh(resume)

    yield AnalysisEvent(
        type="log",
        step="save",
        message="Analysis persisted",
        progress=96,
        status="done",
    )

    message = (
        "Resume analyzed successfully."
        if parsed.get("text_ready")
        else "File saved but text could not be extracted. Try PDF or DOCX."
    )

    yield AnalysisEvent(
        type="result",
        step="complete",
        message=message,
        progress=100,
        status="done",
        detail={
            "id": resume.id,
            "file_name": resume.file_name,
            "ingested": resume.ingested,
            "parsed": parsed,
            "message": message,
        },
    )


async def stream_analysis_events(
    resume: Resume,
    db: Session,
    *,
    step_delay_ms: int = 40,
) -> AsyncIterator[str]:
    """Format analysis events as SSE frames for the client."""
    for event in run_analysis(resume, db):
        payload = event.to_dict()
        payload["ts"] = datetime.now(timezone.utc).isoformat()
        yield f"event: {event.type}\ndata: {json.dumps(payload, default=str)}\n\n"
        if step_delay_ms > 0:
            await asyncio.sleep(step_delay_ms / 1000)
