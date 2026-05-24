"""Bridge from the LiveKit conversational loop into the LangGraph brain.

The brain is interrupted before evaluator (so we keep the interviewer message in
state). The bridge feeds the candidate transcript as `last_answer` and resumes
the graph; the next `interviewer` node emits the next question utterance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.langgraph.graph import get_compiled_graph, thread_config
from app.langgraph.tracing import run_config
from app.services.interview_service import persist_turn
from app.websocket.interview_socket import publish_transcript, schedule_portrait_animation

logger = logging.getLogger("app.livekit_agent.bridge")


class InterviewBridge:
    """Stateful coordinator between LiveKit transcripts and the LangGraph."""

    def __init__(self, interview_id: int, *, candidate_id: int, jd_id: int):
        self.interview_id = interview_id
        self.candidate_id = candidate_id
        self.jd_id = jd_id
        self._graph = get_compiled_graph()
        self._cfg = {**thread_config(interview_id), **run_config(interview_id=interview_id)}
        self._started = False
        self._last_spoken: str = ""

    def _initial_state(self) -> dict[str, Any]:
        return {
            "interview_id": self.interview_id,
            "candidate_id": self.candidate_id,
            "jd_id": self.jd_id,
            "current_q_idx": 0,
            "scores": [],
            "proctor_flags": [],
            "messages": [],
        }

    async def start(self) -> str:
        """Run planner -> interviewer and return the first question."""
        self._started = True
        state = self._initial_state()
        result = await self._graph.ainvoke(state, config=self._cfg)
        reply = self._extract_last_message(result)
        self._last_spoken = reply
        if reply:
            publish_transcript(self.interview_id, "assistant", reply)
            schedule_portrait_animation(self.interview_id, reply)
        return reply

    async def submit_answer(self, answer_text: str) -> str:
        """Inject the candidate's transcript and return the next AI utterance."""
        cleaned = (answer_text or "").strip()
        if not cleaned:
            return self._last_spoken

        if not self._started:
            return await self.start()

        publish_transcript(self.interview_id, "user", cleaned)

        prev = self._graph.get_state(self._cfg)
        prev_values = prev.values if prev else {}
        last_question = str(prev_values.get("last_question") or "")
        scores_before = len(prev_values.get("scores") or [])

        await self._graph.aupdate_state(
            self._cfg, {"last_answer": cleaned}, as_node="interviewer"
        )
        result = await self._graph.ainvoke(None, config=self._cfg)
        reply = self._extract_last_message(result)
        self._last_spoken = reply

        self._persist_latest_turn(cleaned, last_question, scores_before)

        if reply:
            publish_transcript(self.interview_id, "assistant", reply)
            schedule_portrait_animation(self.interview_id, reply)
        return reply

    def _persist_latest_turn(
        self,
        answer_text: str,
        fallback_question: str,
        scores_before: int,
    ) -> None:
        state = self._graph.get_state(self._cfg)
        if not state or not state.values:
            return

        scores = list(state.values.get("scores") or [])
        if len(scores) <= scores_before:
            return

        entry = scores[-1]
        question = str(entry.get("question") or fallback_question or "")
        idx = int(entry.get("idx", len(scores) - 1))
        skill_tag = entry.get("skill_tag")

        score_payload = {
            k: v
            for k, v in entry.items()
            if k not in {"idx", "skill_tag", "question", "answer"}
        }

        try:
            persist_turn(
                self.interview_id,
                idx=idx,
                question=question,
                answer_text=answer_text,
                skill_tag=str(skill_tag) if skill_tag else None,
                score=score_payload,
                answered_at=datetime.now(timezone.utc),
            )
            publish_transcript(
                self.interview_id,
                "system",
                f"Saved Q{idx + 1}: {question[:120]}…",
            )
        except Exception as exc:
            logger.error("persist_turn failed: %s", exc)

    async def report(self) -> dict | None:
        state = self._graph.get_state(self._cfg)
        if not state or not state.values:
            return None
        return state.values.get("report")

    def _extract_last_message(self, state: dict | None) -> str:
        if not state:
            return ""
        msgs = state.get("messages") or []
        if not msgs:
            return ""
        last = msgs[-1]
        return getattr(last, "content", str(last))
