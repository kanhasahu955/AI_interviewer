"""RQ job: generate LivePortrait clip for an assistant utterance."""

from __future__ import annotations

import asyncio
import logging

from app.services.liveportrait_service import animate_interviewer_portrait
from app.websocket.interview_socket import publish_portrait_clip, publish_transcript

logger = logging.getLogger("app.jobs.portrait_animate")


def animate_portrait_job(interview_id: int, text: str) -> None:
    result = asyncio.run(animate_interviewer_portrait(interview_id, text))
    if not result or not result.get("url"):
        return
    publish_portrait_clip(
        interview_id,
        url=str(result["url"]),
        emotion=str(result.get("emotion") or "neutral"),
        content=text,
    )
