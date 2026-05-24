"""LangChain tools usable by interview agents."""

from __future__ import annotations

from langchain_core.tools import tool

from app.rag.retriever import InterviewRetriever, format_context


@tool("rag_search", return_direct=False)
def rag_search(query: str, interview_id: int, top_k: int = 5) -> str:
    """Search resume + JD chunks for the given interview.

    Args:
        query: natural-language search query.
        interview_id: id of the current interview session.
        top_k: number of chunks to return.
    """
    retriever = InterviewRetriever()
    hits = retriever.search(
        query, interview_id=interview_id, top_k=top_k, score_threshold=0.0
    )
    return format_context(hits) or "(no results)"


@tool("read_resume", return_direct=False)
def read_resume(interview_id: int) -> str:
    """Return the top resume chunks for this interview."""
    retriever = InterviewRetriever()
    hits = retriever.search(
        "candidate background, work experience, projects",
        interview_id=interview_id,
        kinds=("resume",),
        top_k=8,
        score_threshold=0.0,
    )
    return format_context(hits) or "(no resume available)"


@tool("read_jd", return_direct=False)
def read_jd(interview_id: int) -> str:
    """Return the top JD chunks for this interview."""
    retriever = InterviewRetriever()
    hits = retriever.search(
        "role responsibilities, required skills, seniority",
        interview_id=interview_id,
        kinds=("jd",),
        top_k=8,
        score_threshold=0.0,
    )
    return format_context(hits) or "(no JD available)"


@tool("flag_candidate", return_direct=False)
def flag_candidate(interview_id: int, reason: str) -> str:
    """Flag the interview for human review (proctoring or integrity concerns)."""
    from app.services.interview_service import flag_interview

    flag_interview(interview_id, reason=reason)
    return f"flagged interview {interview_id}: {reason}"


@tool("end_interview", return_direct=False)
def end_interview(interview_id: int) -> str:
    """End the interview session."""
    from app.services.interview_service import end_interview as svc_end

    svc_end(interview_id)
    return f"ended interview {interview_id}"


ALL_TOOLS = [rag_search, read_resume, read_jd, flag_candidate, end_interview]
