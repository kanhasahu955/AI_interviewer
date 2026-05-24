"""SSE chat fallback (text-only interview mode)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.middlewares.auth import get_current_user
from app.models.user import User
from app.streaming.sse import create_llm_stream

router = APIRouter()


@router.get("/chat")
def chat_stream(
    prompt: str = Query(..., min_length=1, max_length=4000),
    _user: User = Depends(get_current_user),
):
    return create_llm_stream(prompt)
