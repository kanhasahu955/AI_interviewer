from typing import AsyncGenerator

from app.core.llm import get_chat_llm, llm_configured


async def stream_llm_response(prompt: str) -> AsyncGenerator[str, None]:
    if not llm_configured():
        yield "data: GROQ_API_KEY is not configured\n\n"
        return

    llm = get_chat_llm(streaming=True)
    async for chunk in llm.astream(prompt):
        if chunk.content:
            yield f"data: {chunk.content}\n\n"
