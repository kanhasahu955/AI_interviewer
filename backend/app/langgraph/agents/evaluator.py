"""Evaluator agent: scores the last answer and decides probe vs advance."""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_chat_llm
from app.langgraph.state import InterviewState, TurnScore
from app.langgraph.tracing import run_config
from app.prompts import EVALUATOR_SYSTEM

logger = logging.getLogger("app.agents.evaluator")


def evaluator_node(state: InterviewState) -> dict:
    answer = state.get("last_answer")
    if not answer:
        return {"next": "interviewer"}

    plan = state.get("plan") or {"questions": []}
    questions = plan.get("questions") or []
    idx = int(state.get("current_q_idx") or 0)
    q = questions[idx] if 0 <= idx < len(questions) else {}

    llm = get_chat_llm(
        provider="openai" if _openai_available() else None,
        streaming=False,
        temperature=0.0,
    ).with_structured_output(TurnScore)

    rubric_lines = "\n".join(f"- {b}" for b in (q.get("rubric") or []))
    user = (
        f"Question:\n{state.get('last_question') or q.get('question')}\n\n"
        f"Rubric:\n{rubric_lines or '(none)'}\n\n"
        f"Candidate answer:\n{answer}\n"
    )

    try:
        score: TurnScore = llm.invoke(
            [SystemMessage(content=EVALUATOR_SYSTEM), HumanMessage(content=user)],
            config=run_config(
                interview_id=state.get("interview_id"), tags=["evaluator"]
            ),
        )
        score_dict = score.model_dump()
    except Exception as exc:
        logger.warning("evaluator failed: %s", exc)
        score_dict = {
            "correctness": 0.0,
            "depth": 0.0,
            "clarity": 0.0,
            "communication": 0.0,
            "overall": 0.0,
            "feedback": f"evaluator_error: {exc}",
            "probe_followup": False,
            "followup_question": None,
        }

    scores = list(state.get("scores") or [])
    scores.append(
        {
            "idx": idx,
            "skill_tag": q.get("skill_tag"),
            "question": state.get("last_question") or q.get("question"),
            "answer": answer,
            **score_dict,
        }
    )

    advance = not score_dict.get("probe_followup", False)
    next_idx = idx + 1 if advance else idx

    return {
        "last_score": score_dict,
        "scores": scores,
        "current_q_idx": next_idx,
        "last_answer": None,
        "next": "interviewer",
    }


def _openai_available() -> bool:
    from app.core.config import settings

    return bool(settings.OPENAI_API_KEY)
