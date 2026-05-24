from fastapi.responses import StreamingResponse

from app.streaming.llm_stream import (
    stream_llm_response,
)


def create_llm_stream(
    prompt: str,
):

    return StreamingResponse(
        stream_llm_response(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )