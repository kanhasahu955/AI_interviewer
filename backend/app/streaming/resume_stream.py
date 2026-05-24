"""SSE helpers for resume analysis streaming."""

from __future__ import annotations

from fastapi.responses import StreamingResponse

from app.services.resume_analysis_runner import stream_analysis_events


def create_resume_analysis_stream(resume, db) -> StreamingResponse:
    return StreamingResponse(
        stream_analysis_events(resume, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
