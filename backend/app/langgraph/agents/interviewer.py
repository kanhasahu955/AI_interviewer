"""Interviewer agent: utters the next question to the candidate."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.llm import get_chat_llm
from app.langgraph.state import InterviewState
from app.langgraph.tracing import run_config
from app.prompts import INTERVIEWER_SYSTEM

logger = logging.getLogger("app.agents.interviewer")


def interviewer_node(state: InterviewState) -> dict:
    plan = state.get("plan") or {"questions": []}
    questions = plan.get("questions") or []
    idx = int(state.get("current_q_idx") or 0)

    last_score = state.get("last_score") or {}
    probe = last_score.get("probe_followup") and last_score.get("followup_question")

    if not probe and idx >= len(questions):
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Thanks for your time today. That's all the questions I had — "
                        "we'll be in touch with next steps soon."
                    )
                )
            ],
            "next": "reporter",
        }

    if probe:
        question_text = last_score["followup_question"]
        skill_tag = (questions[max(0, idx - 1)] or {}).get("skill_tag")
    else:
        q = questions[idx]
        question_text = q["question"]
        skill_tag = q.get("skill_tag")

    history_snippet = ""
    if state.get("last_answer"):
        history_snippet = (
            f"Candidate's last answer:\n{state['last_answer']}\n\n"
            "Briefly acknowledge it, then ask the next question."
        )

    llm = get_chat_llm(streaming=False, temperature=0.6)
    try:
        rendered = llm.invoke(
            [
                SystemMessage(content=INTERVIEWER_SYSTEM),
                HumanMessage(
                    content=(
                        f"{history_snippet}\n\n"
                        f"Next question to ask (skill: {skill_tag}):\n{question_text}\n\n"
                        "Phrase it as the live interviewer would speak it."
                    )
                ),
            ],
            config=run_config(
                interview_id=state.get("interview_id"), tags=["interviewer"]
            ),
        )
        spoken = rendered.content if hasattr(rendered, "content") else str(rendered)
    except Exception as exc:
        logger.warning("interviewer rendering failed: %s", exc)
        spoken = question_text

    return {
        "messages": [AIMessage(content=spoken)],
        "last_question": spoken,
        "next": "evaluator",
    }
