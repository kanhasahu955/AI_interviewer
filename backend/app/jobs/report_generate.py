"""Background job: run the Reporter agent post-session and persist a Report."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlmodel import Session

from app.core.database import engine
from app.langgraph.agents.reporter import reporter_node
from app.models.interview import Interview, InterviewStatus
from app.models.report import Recommendation, Report
from app.services.interview_service import list_proctor_events, list_turns

logger = logging.getLogger("app.jobs.report_generate")


def generate_report_job(interview_id: int) -> dict:
    if engine is None:
        raise RuntimeError("DB engine not initialised")

    turns = list_turns(interview_id)
    proctor_events = list_proctor_events(interview_id)

    state = {
        "interview_id": interview_id,
        "scores": [
            {
                "idx": t.idx,
                "skill_tag": t.skill_tag,
                "question": t.question,
                "answer": t.answer_text or "",
                **(t.score or {}),
            }
            for t in turns
        ],
        "proctor_flags": [
            {
                "kind": e.kind.value if hasattr(e.kind, "value") else str(e.kind),
                "severity": e.severity.value
                if hasattr(e.severity, "value")
                else str(e.severity),
                "ts": e.ts.isoformat() if e.ts else None,
                "payload": e.payload or {},
            }
            for e in proctor_events
        ],
    }

    result = reporter_node(state)
    report = result.get("report") or {}

    with Session(engine) as s:
        existing = s.get(Report, interview_id)
        if existing:
            s.delete(existing)
            s.commit()

        try:
            recommendation = Recommendation(report.get("recommendation", "borderline"))
        except ValueError:
            recommendation = Recommendation.borderline

        row = Report(
            interview_id=interview_id,
            summary=report.get("summary", ""),
            strengths="\n".join(report.get("strengths") or []),
            weaknesses="\n".join(report.get("weaknesses") or []),
            scores=report.get("per_skill_scores") or {},
            recommendation=recommendation,
            overall_score=float(report.get("overall_score", 0.0)),
            generated_at=datetime.now(timezone.utc),
        )
        s.add(row)

        interview = s.get(Interview, interview_id)
        if interview and interview.status == InterviewStatus.live:
            interview.status = InterviewStatus.completed
            interview.ended_at = datetime.now(timezone.utc)
            s.add(interview)

        s.commit()
        s.refresh(row)
        return {"report_id": row.id, "interview_id": interview_id}
