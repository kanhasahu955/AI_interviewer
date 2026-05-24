"""Proctor agent: aggregates proctoring flags for the interview state.

The actual frame/audio analysis runs in app/proctoring/. This agent only
summarises what's been detected and surfaces it into LangGraph state so the
reporter can downgrade a flagged session.
"""

from __future__ import annotations

import logging

from app.langgraph.state import InterviewState

logger = logging.getLogger("app.agents.proctor")


def proctor_node(state: InterviewState) -> dict:
    flags = list(state.get("proctor_flags") or [])
    critical = sum(1 for f in flags if f.get("severity") == "critical")
    if critical:
        logger.warning(
            "proctor: %d critical flags during interview=%s",
            critical,
            state.get("interview_id"),
        )
    return {"proctor_flags": flags, "next": "interviewer"}


def absorb_event(state: dict, event: dict) -> dict:
    """Append a proctoring event into LangGraph state (used outside the graph)."""
    flags = list(state.get("proctor_flags") or [])
    flags.append(event)
    return {"proctor_flags": flags}
