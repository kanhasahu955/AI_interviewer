"""Interview lifecycle helpers used by routes, agents, and background jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.database import engine
from app.models.interview import Interview, InterviewStatus
from app.models.proctoring_event import (
    ProctoringEvent,
    ProctoringKind,
    ProctoringSeverity,
)
from app.models.turn import Turn

logger = logging.getLogger("app.services.interview")


def _session() -> Session:
    if engine is None:
        raise RuntimeError("DB engine not initialised")
    return Session(engine)


def get_interview(interview_id: int) -> Interview | None:
    with _session() as s:
        return s.get(Interview, interview_id)


def update_status(interview_id: int, status: InterviewStatus) -> None:
    with _session() as s:
        row = s.get(Interview, interview_id)
        if not row:
            return
        row.status = status
        if status == InterviewStatus.live and not row.started_at:
            row.started_at = datetime.now(timezone.utc)
        if status in (InterviewStatus.completed, InterviewStatus.cancelled):
            row.ended_at = datetime.now(timezone.utc)
        s.add(row)
        s.commit()


def start_interview(interview_id: int) -> None:
    update_status(interview_id, InterviewStatus.live)


def end_interview(interview_id: int) -> None:
    update_status(interview_id, InterviewStatus.completed)


def flag_interview(interview_id: int, reason: str) -> None:
    with _session() as s:
        row = s.get(Interview, interview_id)
        if not row:
            return
        row.status = InterviewStatus.flagged
        row.notes = (row.notes or "") + f"\n[flag] {reason}"
        s.add(row)
        s.commit()


def persist_turn(
    interview_id: int,
    *,
    idx: int,
    question: str,
    answer_text: str | None,
    skill_tag: str | None,
    score: dict | None,
    started_at: datetime | None = None,
    answered_at: datetime | None = None,
) -> Turn:
    with _session() as s:
        turn = Turn(
            interview_id=interview_id,
            idx=idx,
            skill_tag=skill_tag,
            question=question,
            answer_text=answer_text,
            score=score,
            started_at=started_at,
            answered_at=answered_at,
        )
        s.add(turn)
        s.commit()
        s.refresh(turn)
        return turn


def list_turns(interview_id: int) -> list[Turn]:
    with _session() as s:
        return list(
            s.exec(
                select(Turn).where(Turn.interview_id == interview_id).order_by(Turn.idx)
            )
        )


def record_proctor_event(
    interview_id: int,
    *,
    kind: ProctoringKind,
    severity: ProctoringSeverity = ProctoringSeverity.info,
    payload: dict | None = None,
    ts: datetime | None = None,
    publish: bool = True,
) -> ProctoringEvent:
    with _session() as s:
        evt = ProctoringEvent(
            interview_id=interview_id,
            kind=kind,
            severity=severity,
            payload=payload,
            ts=ts or datetime.now(timezone.utc),
        )
        s.add(evt)
        s.commit()
        s.refresh(evt)

    if publish:
        publish_proctor_event(interview_id, evt, payload or {})

    return evt


def publish_proctor_event(
    interview_id: int,
    evt: ProctoringEvent,
    payload: dict | None = None,
) -> None:
    """Broadcast a proctor event to recruiter/candidate dashboards via Redis."""
    import json

    try:
        from app.core.redis_client import get_redis

        message = {
            "id": evt.id,
            "interview_id": interview_id,
            "kind": evt.kind.value if hasattr(evt.kind, "value") else str(evt.kind),
            "severity": evt.severity.value
            if hasattr(evt.severity, "value")
            else str(evt.severity),
            "ts": evt.ts.isoformat() if evt.ts else datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        get_redis().publish(f"proctor:{interview_id}", json.dumps(message))
    except Exception as exc:
        logger.debug("proctor redis publish skipped: %s", exc)


def list_proctor_events(interview_id: int) -> list[ProctoringEvent]:
    with _session() as s:
        return list(
            s.exec(
                select(ProctoringEvent)
                .where(ProctoringEvent.interview_id == interview_id)
                .order_by(ProctoringEvent.ts)
            )
        )
