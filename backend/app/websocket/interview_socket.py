"""Recruiter dashboard websocket: live transcript + proctor alerts.

A recruiter connects to /ws/interviews/{interview_id} after authenticating with
`?token=<access_token>`. We subscribe to two Redis pub/sub channels (`proctor:{id}`
and `transcript:{id}`) and relay every message into the open websocket.
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from sqlmodel import Session

from app.core.database import engine
from app.core.redis_client import get_redis
from app.core.security import decode_access_token
from app.models.interview import Interview
from app.models.job_description import JobDescription
from app.models.user import User, UserRole
from app.websocket.manager import manager

router = APIRouter()
logger = logging.getLogger("app.websocket.interview")


def _authorise(token: str, interview_id: int) -> User:
    payload = decode_access_token(token)
    user_id = int(payload.get("sub", 0) or 0)
    if not user_id or engine is None:
        raise PermissionError("invalid token")

    with Session(engine) as s:
        user = s.get(User, user_id)
        if not user or not user.is_active:
            raise PermissionError("inactive user")
        interview = s.get(Interview, interview_id)
        if not interview:
            raise PermissionError("interview not found")
        if user.role == UserRole.admin:
            return user
        if user.role == UserRole.candidate and interview.candidate_id == user.id:
            return user
        if user.role == UserRole.recruiter:
            jd = s.get(JobDescription, interview.jd_id)
            if jd and jd.recruiter_id == user.id:
                return user
        raise PermissionError("forbidden")


@router.websocket("/ws/interviews/{interview_id}")
async def interview_ws(
    websocket: WebSocket,
    interview_id: int,
    token: str = Query(...),
):
    client = websocket.client.host if websocket.client else "?"
    try:
        user = _authorise(token, interview_id)
    except Exception as exc:
        logger.warning(
            "[yellow]WS REJECTED[/] /ws/interviews/%s  from=%s  reason=%s",
            interview_id,
            client,
            exc,
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc))
        return

    room = f"interview-{interview_id}"
    await manager.connect(websocket, room)
    logger.info(
        "[green]WS CONNECT[/] /ws/interviews/%s  user=%s(%s)  from=%s  room=%s",
        interview_id,
        user.id,
        user.role.value,
        client,
        room,
    )
    pubsub_task = asyncio.create_task(_relay_pubsub(websocket, interview_id))
    try:
        while True:
            msg = await websocket.receive_json()
            if not isinstance(msg, dict):
                continue
            msg["from"] = f"user-{user.id}"
            await manager.send_to_room(room, msg)
    except WebSocketDisconnect:
        pass
    finally:
        pubsub_task.cancel()
        try:
            await pubsub_task
        except (asyncio.CancelledError, Exception):
            pass
        manager.disconnect(websocket, room)
        logger.info(
            "[dim]WS DISCONNECT[/] /ws/interviews/%s  user=%s",
            interview_id,
            user.id,
        )


async def _relay_pubsub(websocket: WebSocket, interview_id: int) -> None:
    try:
        redis = get_redis()
        pubsub = redis.pubsub()
        channels = [f"proctor:{interview_id}", f"transcript:{interview_id}", f"portrait:{interview_id}"]
        pubsub.subscribe(*channels)
    except Exception as exc:
        logger.warning("redis pubsub unavailable: %s", exc)
        return

    loop = asyncio.get_running_loop()

    def _next_message():
        return pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

    try:
        while True:
            msg = await loop.run_in_executor(None, _next_message)
            if not msg:
                await asyncio.sleep(0.05)
                continue
            data = msg.get("data")
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8", errors="ignore")
            try:
                payload = json.loads(data) if isinstance(data, str) else data
            except Exception:
                payload = {"raw": data}
            try:
                await websocket.send_json(
                    {"channel": msg.get("channel", b"").decode() if isinstance(msg.get("channel"), (bytes, bytearray)) else msg.get("channel"), "data": payload}
                )
            except Exception:
                break
    finally:
        try:
            pubsub.close()
        except Exception:
            pass


def publish_transcript(
    interview_id: int,
    role: str,
    content: str,
    *,
    portrait_url: str | None = None,
    emotion: str | None = None,
) -> None:
    """Helper used by the LiveKit worker to push transcripts to dashboards."""
    try:
        payload: dict[str, str] = {"role": role, "content": content}
        if portrait_url:
            payload["portrait_url"] = portrait_url
        if emotion:
            payload["emotion"] = emotion
        redis = get_redis()
        redis.publish(
            f"transcript:{interview_id}",
            json.dumps(payload),
        )
    except Exception as exc:
        logger.debug("publish_transcript skipped: %s", exc)


def publish_portrait_clip(
    interview_id: int,
    *,
    url: str,
    emotion: str | None = None,
    content: str | None = None,
) -> None:
    try:
        payload: dict[str, str] = {"url": url}
        if emotion:
            payload["emotion"] = emotion
        if content:
            payload["content"] = content
        redis = get_redis()
        redis.publish(f"portrait:{interview_id}", json.dumps(payload))
    except Exception as exc:
        logger.debug("publish_portrait_clip skipped: %s", exc)


def schedule_portrait_animation(interview_id: int, text: str) -> None:
    """Queue LivePortrait generation for an assistant utterance (non-blocking)."""
    from app.core.config import settings

    if not settings.LIVEPORTRAIT_ENABLED:
        return
    cleaned = (text or "").strip()
    if not cleaned:
        return

    if settings.USE_REDIS_QUEUE:
        try:
            from app.jobs.worker import enqueue

            enqueue("app.jobs.portrait_animate.animate_portrait_job", interview_id, cleaned)
        except Exception as exc:
            logger.debug("portrait enqueue failed: %s", exc)
    else:
        import threading

        def _run() -> None:
            from app.jobs.portrait_animate import animate_portrait_job

            try:
                animate_portrait_job(interview_id, cleaned)
            except Exception as exc:
                logger.warning("portrait animation thread failed: %s", exc)

        threading.Thread(target=_run, daemon=True).start()
