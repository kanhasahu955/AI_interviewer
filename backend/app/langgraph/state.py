"""Shared state schema for the interview LangGraph."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class PlannedQuestion(BaseModel):
    """A single planned interview question."""

    skill_tag: str = Field(description="Skill or competency this question targets.")
    question: str = Field(description="The question to ask the candidate.")
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    rationale: str | None = None
    rubric: list[str] = Field(
        default_factory=list,
        description="Bullet points describing a strong answer.",
    )


class QuestionPlan(BaseModel):
    """Full ordered interview plan produced by the planner agent."""

    questions: list[PlannedQuestion]
    total_minutes: int = 30
    summary: str | None = None


class TurnScore(BaseModel):
    """Per-turn rubric scoring produced by the evaluator."""

    correctness: float = Field(ge=0.0, le=10.0)
    depth: float = Field(ge=0.0, le=10.0)
    clarity: float = Field(ge=0.0, le=10.0)
    communication: float = Field(ge=0.0, le=10.0)
    overall: float = Field(ge=0.0, le=10.0)
    feedback: str
    probe_followup: bool = False
    followup_question: str | None = None


class FinalReport(BaseModel):
    """Final report produced by the reporter agent."""

    summary: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    per_skill_scores: dict[str, float] = Field(default_factory=dict)
    overall_score: float = 0.0
    recommendation: Literal[
        "strong_hire", "hire", "borderline", "no_hire"
    ] = "borderline"


class InterviewState(TypedDict, total=False):
    """The full interview-runtime state managed by LangGraph."""

    interview_id: int
    candidate_id: int
    jd_id: int
    resume_id: int | None

    plan: dict | None
    current_q_idx: int
    last_question: str | None
    last_answer: str | None
    last_score: dict | None
    scores: list[dict]
    proctor_flags: list[dict]
    retrieved_ctx: str | None
    report: dict | None

    messages: Annotated[list, add_messages]
    next: Literal[
        "planner",
        "interviewer",
        "evaluator",
        "reporter",
        "end",
    ]
