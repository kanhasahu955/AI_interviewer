"""LLM provider factory used by agents, streaming, and the LiveKit worker."""

from __future__ import annotations

from typing import Literal

from app.core.config import settings

Provider = Literal["groq", "openai", "anthropic", "google"]


def llm_configured(provider: Provider = "groq") -> bool:
    return {
        "groq": bool(settings.GROQ_API_KEY),
        "openai": bool(settings.OPENAI_API_KEY),
        "anthropic": bool(settings.ANTHROPIC_API_KEY),
        "google": bool(settings.GOOGLE_API_KEY),
    }.get(provider, False)


def get_chat_llm(
    *,
    provider: Provider | None = None,
    streaming: bool = False,
    temperature: float = 0.3,
    model: str | None = None,
):
    """Return a LangChain chat model for the requested provider."""
    provider = provider or _default_provider()

    if provider == "groq":
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured")
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=model or settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            streaming=streaming,
            temperature=temperature,
        )

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or "gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            streaming=streaming,
            temperature=temperature,
        )

    if provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model or settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            streaming=streaming,
            temperature=temperature,
        )

    if provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY is not configured")
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model or settings.GOOGLE_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature,
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")


def _default_provider() -> Provider:
    if settings.GROQ_API_KEY:
        return "groq"
    if settings.OPENAI_API_KEY:
        return "openai"
    if settings.ANTHROPIC_API_KEY:
        return "anthropic"
    if settings.GOOGLE_API_KEY:
        return "google"
    raise RuntimeError("No LLM provider configured")
