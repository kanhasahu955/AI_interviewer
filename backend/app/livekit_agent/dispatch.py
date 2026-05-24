"""LiveKit room + token helpers used by the FastAPI routes."""

from __future__ import annotations

import logging
from datetime import timedelta

from app.core.config import settings

logger = logging.getLogger("app.livekit_agent.dispatch")


def room_name_for(interview_id: int | str) -> str:
    return f"interview-{interview_id}"


def _ensure_configured() -> None:
    if not (settings.LIVEKIT_URL and settings.LIVEKIT_API_KEY and settings.LIVEKIT_API_SECRET):
        raise RuntimeError("LiveKit credentials are not configured")


def issue_candidate_token(
    interview_id: int | str,
    *,
    identity: str,
    name: str | None = None,
    ttl_minutes: int = 60,
) -> dict:
    """Mint a LiveKit access token for the candidate joining the room."""
    _ensure_configured()
    from livekit import api

    room = room_name_for(interview_id)

    grants = api.VideoGrants(
        room_join=True,
        room=room,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )

    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(name or identity)
        .with_grants(grants)
        .with_ttl(timedelta(minutes=ttl_minutes))
        .to_jwt()
    )

    return {
        "url": settings.LIVEKIT_URL,
        "room": room,
        "identity": identity,
        "token": token,
    }


def issue_agent_token(
    interview_id: int | str, *, identity: str = "ai-interviewer", ttl_minutes: int = 60
) -> dict:
    """Mint a token for the AI worker joining the same room as a participant."""
    _ensure_configured()
    from livekit import api

    room = room_name_for(interview_id)

    grants = api.VideoGrants(
        room_join=True,
        room=room,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
        agent=True,
    )

    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name("AI Interviewer")
        .with_grants(grants)
        .with_ttl(timedelta(minutes=ttl_minutes))
        .to_jwt()
    )

    return {
        "url": settings.LIVEKIT_URL,
        "room": room,
        "identity": identity,
        "token": token,
    }


async def ensure_room(interview_id: int | str) -> str:
    """Create the LiveKit room (idempotent) and return its name."""
    _ensure_configured()
    from livekit import api

    room = room_name_for(interview_id)
    livekit_api = api.LiveKitAPI(
        settings.LIVEKIT_URL,
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET,
    )
    try:
        await livekit_api.room.create_room(
            api.CreateRoomRequest(name=room, empty_timeout=300, max_participants=4)
        )
    except Exception as exc:
        logger.debug("ensure_room: %s (likely already exists)", exc)
    finally:
        try:
            await livekit_api.aclose()
        except Exception:
            pass
    return room
