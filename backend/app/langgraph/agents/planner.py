"""Planner agent: builds an ordered interview question plan."""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_chat_llm
from app.langgraph.state import InterviewState, QuestionPlan
from app.langgraph.tracing import run_config
from app.prompts import PLANNER_SYSTEM
from app.rag.retriever import InterviewRetriever, format_context

logger = logging.getLogger("app.agents.planner")


def _gather_context(interview_id: int) -> str:
    try:
        retriever = InterviewRetriever()
        hits = retriever.search(
            "summarize the candidate's experience and the role requirements",
            interview_id=interview_id,
            kinds=("resume", "jd"),
            top_k=12,
            score_threshold=0.0,
        )
        context = format_context(hits)
        if context.strip():
            return context
    except Exception as exc:
        logger.warning("planner: RAG unavailable: %s", exc)
    return _load_context_from_db(interview_id)


def _load_context_from_db(interview_id: int) -> str:
    """Fallback when Pinecone ingest is pending or unavailable."""
    from sqlmodel import Session

    from app.core.database import engine
    from app.models.interview import Interview
    from app.models.job_description import JobDescription
    from app.models.resume import Resume
    from app.services.resume_analyzer import sanitize_resume_text

    if engine is None:
        return ""

    parts: list[str] = []
    with Session(engine) as s:
        interview = s.get(Interview, interview_id)
        if not interview:
            return ""
        if interview.resume_id:
            resume = s.get(Resume, interview.resume_id)
            if resume:
                text = sanitize_resume_text(resume.raw_text or "")
                if text:
                    parts.append(f"RESUME ({resume.file_name}):\n{text[:12000]}")
                elif resume.parsed:
                    skills = resume.parsed.get("skills_detected") or []
                    parts.append(
                        "RESUME SKILLS:\n" + ", ".join(str(x) for x in skills)
                    )
        jd = s.get(JobDescription, interview.jd_id)
        if jd:
            parts.append(f"JOB DESCRIPTION ({jd.title}):\n{jd.raw_text[:6000]}")
    return "\n\n".join(parts)


def planner_node(state: InterviewState) -> dict:
    interview_id = int(state["interview_id"])
    context = _gather_context(interview_id)

    llm = get_chat_llm(streaming=False, temperature=0.4).with_structured_output(
        QuestionPlan
    )

    user_msg = (
        "Build the interview plan now.\n\n"
        f"Retrieved context (resume + JD):\n{context or '(no context available)'}"
    )

    try:
        plan: QuestionPlan = llm.invoke(
            [SystemMessage(content=PLANNER_SYSTEM), HumanMessage(content=user_msg)],
            config=run_config(interview_id=interview_id, tags=["planner"]),
        )
    except Exception as exc:
        logger.error("planner failed: %s", exc)
        plan = QuestionPlan(
            questions=[],
            summary=f"planner_error: {exc}",
        )

    logger.info("planner produced %d questions", len(plan.questions))
    return {
        "plan": plan.model_dump(),
        "current_q_idx": 0,
        "retrieved_ctx": context,
        "next": "interviewer",
    }
