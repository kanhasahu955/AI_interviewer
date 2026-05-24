"""StateGraph wiring for the interview multi-agent flow."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.langgraph.agents.evaluator import evaluator_node
from app.langgraph.agents.interviewer import interviewer_node
from app.langgraph.agents.planner import planner_node
from app.langgraph.agents.reporter import reporter_node
from app.langgraph.state import InterviewState

logger = logging.getLogger("app.langgraph.graph")


def _route_after_interviewer(
    state: InterviewState,
) -> Literal["evaluator", "reporter"]:
    nxt = state.get("next")
    if nxt == "reporter":
        return "reporter"
    return "evaluator"


def _route_after_evaluator(state: InterviewState) -> Literal["interviewer"]:
    return "interviewer"


def _route_after_planner(state: InterviewState) -> Literal["interviewer"]:
    return "interviewer"


def build_graph():
    g = StateGraph(InterviewState)
    g.add_node("planner", planner_node)
    g.add_node("interviewer", interviewer_node)
    g.add_node("evaluator", evaluator_node)
    g.add_node("reporter", reporter_node)

    g.add_edge(START, "planner")
    g.add_conditional_edges("planner", _route_after_planner, {"interviewer": "interviewer"})
    g.add_conditional_edges(
        "interviewer",
        _route_after_interviewer,
        {"evaluator": "evaluator", "reporter": "reporter"},
    )
    g.add_conditional_edges(
        "evaluator", _route_after_evaluator, {"interviewer": "interviewer"}
    )
    g.add_edge("reporter", END)

    return g


@lru_cache(maxsize=1)
def get_compiled_graph():
    checkpointer = MemorySaver()
    return build_graph().compile(checkpointer=checkpointer, interrupt_before=["evaluator"])


def thread_config(interview_id: int) -> dict:
    return {"configurable": {"thread_id": f"interview-{interview_id}"}}
