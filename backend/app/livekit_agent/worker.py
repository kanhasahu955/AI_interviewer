"""LiveKit Agents worker entrypoint.

Run with:
    python -m app.livekit_agent.worker dev
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncGenerator

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.livekit_agent.frames import consume_video
from app.livekit_agent.llm_bridge import InterviewBridge
from app.proctoring.pipeline import ProctorPipeline
from app.services.interview_service import (
    end_interview,
    get_interview,
    start_interview,
)

setup_logging()
logger = logging.getLogger("app.livekit_agent.worker")

INTRO_GREETING = (
    "Hi! I'm Alex, your interviewer today. I'll ask a few questions based on your resume — "
    "please answer out loud when you hear each question."
)

CANDIDATE_JOIN_TIMEOUT_SEC = 180


def _bootstrap_worker_env() -> None:
    """Ensure child processes inherit keys LiveKit plugins read from the environment."""
    if settings.LIVEKIT_URL:
        os.environ.setdefault("LIVEKIT_URL", settings.LIVEKIT_URL)
    if settings.LIVEKIT_API_KEY:
        os.environ.setdefault("LIVEKIT_API_KEY", settings.LIVEKIT_API_KEY)
    if settings.LIVEKIT_API_SECRET:
        os.environ.setdefault("LIVEKIT_API_SECRET", settings.LIVEKIT_API_SECRET)
    if settings.OPENAI_API_KEY:
        os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)
    if settings.SIMLI_API_KEY:
        os.environ.setdefault("SIMLI_API_KEY", settings.SIMLI_API_KEY)
    if settings.SIMLI_FACE_ID:
        os.environ.setdefault("SIMLI_FACE_ID", settings.SIMLI_FACE_ID)


def _interview_id_from_room(room_name: str) -> int | None:
    if not room_name or not room_name.startswith("interview-"):
        return None
    try:
        return int(room_name.split("-", 1)[1])
    except ValueError:
        return None


def _message_text(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
            else:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
        return " ".join(p for p in parts if p).strip()
    return str(content or "")


def _build_interviewer_agent(bridge: InterviewBridge, *, intro: str):
    from livekit.agents import Agent, llm
    from livekit.plugins import openai, silero

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    openai_key = settings.OPENAI_API_KEY
    spoken_intro = intro.strip()

    class _InterviewerAgent(Agent):
        def __init__(self) -> None:
            super().__init__(
                instructions=(
                    "You are Alex, a warm and professional technical interviewer. "
                    "Ask one clear question at a time and listen carefully."
                ),
                stt=openai.STT(
                    model=settings.OPENAI_STT_MODEL,
                    api_key=openai_key,
                ),
                llm=openai.LLM(
                    model="gpt-4o-mini",
                    api_key=openai_key,
                ),
                tts=openai.TTS(
                    model=settings.OPENAI_TTS_MODEL,
                    voice=settings.OPENAI_TTS_VOICE,
                    api_key=openai_key,
                ),
                vad=silero.VAD.load(),
            )
            self._spoken_intro = spoken_intro

        async def on_enter(self) -> None:
            logger.info("Alex joined — speaking intro (%d chars)", len(self._spoken_intro))
            if self._spoken_intro:
                self.session.say(self._spoken_intro, allow_interruptions=True)

        async def on_user_turn_completed(
            self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
        ) -> None:
            text = _message_text(new_message)
            if text:
                logger.info("heard candidate (%d chars): %.120s", len(text), text)

        async def llm_node(
            self,
            chat_ctx: llm.ChatContext,
            tools: list[llm.Tool],
            model_settings,
        ) -> AsyncGenerator[str, None]:
            last_user = ""
            for message in reversed(chat_ctx.items):
                if getattr(message, "role", "") == "user":
                    last_user = _message_text(message)
                    if last_user:
                        break

            if not last_user:
                logger.debug("llm_node: no user message in context")
                return

            try:
                reply = await bridge.submit_answer(last_user)
            except Exception as exc:
                logger.exception("bridge.submit_answer failed: %s", exc)
                reply = (
                    "Thank you for sharing. Could you walk me through your role "
                    "and the main technical challenges on that project?"
                )

            if reply:
                logger.info("TTS: speaking reply (%d chars)", len(reply))
                yield reply

    return _InterviewerAgent()


async def _run_entrypoint(ctx) -> None:
    from livekit import rtc
    from livekit.agents import AgentSession, AutoSubscribe

    room: rtc.Room = ctx.room
    interview_id = _interview_id_from_room(room.name)
    if interview_id is None:
        logger.error("worker: unrecognised room name %s", room.name)
        return

    interview = get_interview(interview_id)
    if interview is None:
        logger.error("worker: interview %s not found", interview_id)
        return

    candidate_identity = f"candidate-{interview.candidate_id}"

    async def _on_shutdown(_reason: str = "") -> None:
        try:
            end_interview(interview_id)
        except Exception as exc:
            logger.warning("end_interview failed: %s", exc)
        if settings.USE_REDIS_QUEUE:
            try:
                from app.jobs.worker import enqueue

                enqueue("app.jobs.report_generate.generate_report_job", interview_id)
            except Exception as exc:
                logger.warning("report enqueue failed: %s", exc)

    ctx.add_shutdown_callback(_on_shutdown)

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    start_interview(interview_id)

    from app.websocket.interview_socket import publish_transcript

    publish_transcript(interview_id, "assistant", INTRO_GREETING)

    bridge = InterviewBridge(
        interview_id=interview_id,
        candidate_id=interview.candidate_id,
        jd_id=interview.jd_id,
    )
    proctor = ProctorPipeline(interview_id)

    first_question = ""
    try:
        first_question = await bridge.start()
        logger.info("planner ready — first question (%d chars)", len(first_question))
    except Exception as exc:
        logger.exception("bridge.start failed; using fallback question: %s", exc)
        first_question = (
            "Welcome! Tell me about a recent project you're proud of and your role on the team."
        )

    intro = INTRO_GREETING
    if first_question:
        intro = f"{INTRO_GREETING} {first_question}"

    from app.websocket.interview_socket import schedule_portrait_animation

    schedule_portrait_animation(interview_id, intro)

    logger.info("waiting for candidate %s (timeout %ss)", candidate_identity, CANDIDATE_JOIN_TIMEOUT_SEC)
    try:
        participant = await asyncio.wait_for(
            ctx.wait_for_participant(identity=candidate_identity),
            timeout=CANDIDATE_JOIN_TIMEOUT_SEC,
        )
        logger.info("candidate joined room: %s", participant.identity)
    except asyncio.TimeoutError:
        logger.error("candidate %s never joined — voice interview aborted", candidate_identity)
        return

    @room.on("track_subscribed")
    def _on_track(track, publication, participant):  # noqa: ANN001
        if participant.identity.startswith("agent") or participant.identity.startswith("ai-"):
            return
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            logger.info("subscribed to candidate video from %s", participant.identity)
            asyncio.create_task(consume_video(track, proctor.on_frame))

    session = await _start_voice_session(
        room,
        bridge,
        intro=intro,
        candidate_identity=candidate_identity,
    )
    if session is None:
        logger.error("voice session failed — candidate will see transcript but hear no audio")
        return

    logger.info("interview %s live — Alex voice session active", interview_id)


def _simli_avatar_configured() -> bool:
    return bool(
        settings.SIMLI_ENABLED
        and settings.SIMLI_API_KEY
        and settings.SIMLI_FACE_ID
    )


async def _start_simli_avatar(session, room) -> tuple[bool, str | None]:
    """Start Simli avatar before AgentSession.start — matches Simli/LiveKit docs."""
    if not _simli_avatar_configured():
        return False, None

    try:
        from livekit import rtc
        from livekit.agents import utils
        from livekit.agents.voice.avatar import DataStreamAudioOutput
        from livekit.plugins import simli
    except Exception as exc:
        msg = f"Simli plugin missing ({exc}). Run: uv add livekit-plugins-simli"
        logger.error(msg)
        return False, msg

    avatar_kwargs: dict = {
        "simli_config": simli.SimliConfig(
            api_key=settings.SIMLI_API_KEY,
            face_id=settings.SIMLI_FACE_ID,
        ),
    }
    if settings.SIMLI_AVATAR_IDENTITY:
        avatar_kwargs["avatar_participant_identity"] = settings.SIMLI_AVATAR_IDENTITY
    if settings.SIMLI_AVATAR_NAME:
        avatar_kwargs["avatar_participant_name"] = settings.SIMLI_AVATAR_NAME

    avatar = simli.AvatarSession(**avatar_kwargs)
    await avatar.start(session, room=room)

    if not isinstance(getattr(session.output, "audio", None), DataStreamAudioOutput):
        logger.error("Simli avatar failed — audio pipeline not connected to avatar")
        return False, (
            "Simli avatar failed to connect. Verify SIMLI_API_KEY and SIMLI_FACE_ID "
            "in backend/.env, then restart make dev and start a new interview."
        )

    identity = avatar.avatar_identity
    logger.info("Simli avatar connecting in %s (identity=%s)", room.name, identity)

    try:
        await asyncio.wait_for(
            utils.wait_for_track_publication(
                room=room,
                identity=identity,
                kind=rtc.TrackKind.KIND_VIDEO,
                include_local=True,
            ),
            timeout=25.0,
        )
        logger.info("Simli avatar video live in %s", room.name)
        return True, None
    except asyncio.TimeoutError:
        msg = (
            "Simli avatar did not publish video within 25s. "
            "Verify SIMLI_FACE_ID matches a face in your Simli dashboard."
        )
        logger.error(msg)
        return False, msg


async def _start_voice_session(
    room,
    bridge: InterviewBridge,
    *,
    intro: str,
    candidate_identity: str,
):
    try:
        from livekit.agents import AgentSession
        from livekit.agents.voice import room_io
        from livekit.plugins import openai, silero  # noqa: F401 — verify plugins installed
    except Exception as exc:
        logger.error(
            "voice plugins missing (%s). Run: uv sync",
            exc,
        )
        return None

    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not configured — voice STT/TTS disabled")
        return None

    try:
        agent = _build_interviewer_agent(bridge, intro=intro)
        # Simli docs: create session → avatar.start → session.start(agent)
        session = AgentSession()
        avatar_started, avatar_err = await _start_simli_avatar(session, room)
        if avatar_err:
            from app.websocket.interview_socket import publish_transcript

            interview_id = _interview_id_from_room(room.name)
            if interview_id is not None:
                publish_transcript(interview_id, "system", avatar_err)

        room_options = room_io.RoomOptions(
            participant_identity=candidate_identity,
            close_on_disconnect=True,
        )
        await session.start(agent, room=room, room_options=room_options)
        logger.info(
            "voice agent session started in %s (listening to %s%s)",
            room.name,
            candidate_identity,
            ", Simli video avatar" if avatar_started else "",
        )
        return session
    except Exception as exc:
        logger.exception("failed to start voice agent session: %s", exc)
        return None


def _cli() -> None:
    from livekit.agents import WorkerOptions, cli

    _bootstrap_worker_env()

    if not settings.LIVEKIT_URL:
        raise SystemExit("LIVEKIT_URL is not configured")

    cli.run_app(WorkerOptions(entrypoint_fnc=_run_entrypoint))


if __name__ == "__main__":
    _cli()
