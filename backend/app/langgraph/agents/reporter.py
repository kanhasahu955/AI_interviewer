"""Reporter agent: synthesises the final interview report."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_chat_llm
from app.langgraph.state import FinalReport, InterviewState
from app.langgraph.tracing import run_config
from app.prompts import REPORTER_SYSTEM

logger = logging.getLogger("app.agents.reporter")


def reporter_node(state: InterviewState) -> dict:
    plan = state.get("plan") or {}
    scores = state.get("scores") or []
    proctor_flags = state.get("proctor_flags") or []

    llm = get_chat_llm(
        provider="openai" if _openai_available() else None,
        streaming=False,
        temperature=0.2,
    ).with_structured_output(FinalReport)

    payload = {
        "plan_summary": plan.get("summary"),
        "scores": scores,
        "proctor_flags": proctor_flags,
        "retrieved_ctx": (state.get("retrieved_ctx") or "")[:6000],
    }

    user = "Write the final report based on this transcript JSON:\n" + json.dumps(
        payload, default=str, indent=2
    )

    try:
        report: FinalReport = llm.invoke(
            [SystemMessage(content=REPORTER_SYSTEM), HumanMessage(content=user)],
            config=run_config(
                interview_id=state.get("interview_id"), tags=["reporter"]
            ),
        )
        report_dict = report.model_dump()
    except Exception as exc:
        logger.error("reporter failed: %s", exc)
        report_dict = {
            "summary": f"reporter_error: {exc}",
            "strengths": [],
            "weaknesses": [],
            "per_skill_scores": {},
            "overall_score": 0.0,
            "recommendation": "borderline",
        }

    return {"report": report_dict, "next": "end"}


def _openai_available() -> bool:
    from app.core.config import settings

    return bool(settings.OPENAI_API_KEY)
