"""faster-whisper STT adapter that plugs into livekit-agents.

Only loaded if both `livekit.agents` and `faster_whisper` are importable. The
implementation is best-effort: we buffer audio between speech-start and
speech-end events, then transcribe synchronously off the event loop.
"""

from __future__ import annotations

import asyncio
import io
import logging
from typing import AsyncIterator

logger = logging.getLogger("app.livekit_agent.whisper_stt")


class FasterWhisperSTT:
    def __init__(self, model_size: str = "base", language: str | None = None):
        from faster_whisper import WhisperModel  # noqa: WPS433

        self._model = WhisperModel(model_size, device="auto", compute_type="auto")
        self._language = language

    async def recognize(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._transcribe, audio_bytes, sample_rate)

    def _transcribe(self, audio_bytes: bytes, sample_rate: int) -> str:
        import numpy as np

        samples = np.frombuffer(audio_bytes, dtype=np.int16).astype("float32") / 32768.0
        segments, _ = self._model.transcribe(samples, language=self._language)
        return " ".join(seg.text.strip() for seg in segments).strip()
