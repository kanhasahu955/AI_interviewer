"""Animate the interviewer portrait from TTS audio using LivePortrait.

Expects a local clone of https://github.com/KwaiVGI/LivePortrait (same tech as
https://liveportrait.org/) with weights installed. Set LIVEPORTRAIT_REPO in `.env`.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import numpy as np

from app.core.config import AI_ROOT, settings

logger = logging.getLogger("app.services.liveportrait")

PORTRAIT_MEDIA_SUBDIR = "portraits"


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = AI_ROOT / path
    return path


def find_liveportrait_repo() -> Path | None:
    if settings.LIVEPORTRAIT_REPO:
        repo = Path(settings.LIVEPORTRAIT_REPO).expanduser()
        if (repo / "inference.py").exists():
            return repo
        logger.warning("LIVEPORTRAIT_REPO set but inference.py missing: %s", repo)

    for candidate in (
        AI_ROOT / "LivePortrait",
        AI_ROOT.parent / "LivePortrait",
        Path.home() / "LivePortrait",
    ):
        if (candidate / "inference.py").exists():
            return candidate
    return None


def portrait_output_dir(interview_id: int) -> Path:
    out = settings.STORAGE_DIR / PORTRAIT_MEDIA_SUBDIR / str(interview_id)
    out.mkdir(parents=True, exist_ok=True)
    return out


def media_url_for(path: Path) -> str:
    rel = path.relative_to(settings.STORAGE_DIR)
    return f"/api/v1/media/{rel.as_posix()}"


def detect_emotion_from_wav(wav_path: Path) -> str:
    """Rough energy-based emotion tag for UI styling."""
    try:
        import librosa

        y, _sr = librosa.load(str(wav_path), sr=16_000, duration=12.0)
        if y.size == 0:
            return "neutral"
        rms = float(np.mean(librosa.feature.rms(y=y)))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=y)))
        if rms > 0.08 and zcr > 0.06:
            return "enthusiastic"
        if rms > 0.045:
            return "warm"
        return "calm"
    except Exception as exc:
        logger.debug("emotion detection skipped: %s", exc)
        return "neutral"


def synthesize_tts_wav(text: str, dest: Path) -> Path:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY required for portrait TTS")

    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with client.audio.speech.with_streaming_response.create(
        model=settings.OPENAI_TTS_MODEL,
        voice=settings.OPENAI_TTS_VOICE,
        input=text[:4096],
        response_format="wav",
    ) as response:
        response.stream_to_file(dest)
    return dest


def _default_driving_video(repo: Path) -> Path | None:
    configured = settings.LIVEPORTRAIT_DRIVING_VIDEO
    if configured:
        path = _resolve_path(configured)
        if path.exists():
            return path

    bundled = _resolve_path("assets/interviewer/driving_talk.mp4")
    if bundled.exists():
        return bundled

    sample = repo / "assets/examples/driving/d0.mp4"
    return sample if sample.exists() else None


def _run_liveportrait(
    repo: Path,
    *,
    source_image: Path,
    driving_video: Path,
    output_dir: Path,
) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(repo / "inference.py"),
        "-s",
        str(source_image),
        "-d",
        str(driving_video),
        "-o",
        str(output_dir),
    ]
    logger.info("LivePortrait: %s", " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=settings.LIVEPORTRAIT_TIMEOUT_SEC,
    )
    if proc.returncode != 0:
        logger.error(
            "LivePortrait failed (code %s)\nstdout: %s\nstderr: %s",
            proc.returncode,
            proc.stdout[-2000:] if proc.stdout else "",
            proc.stderr[-2000:] if proc.stderr else "",
        )
        return None

    mp4s = sorted(output_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if mp4s:
        return mp4s[0]

    # inference.py may write into a nested animations folder
    nested = sorted(output_dir.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return nested[0] if nested else None


async def animate_interviewer_portrait(
    interview_id: int,
    text: str,
) -> dict | None:
    """Generate a lip-synced portrait clip; return metadata for the client."""
    cleaned = (text or "").strip()
    if not cleaned or not settings.LIVEPORTRAIT_ENABLED:
        return None

    repo = find_liveportrait_repo()
    if repo is None:
        logger.debug("LivePortrait repo not found — skipping animation")
        return None

    source = _resolve_path(settings.LIVEPORTRAIT_SOURCE_IMAGE)
    if not source.exists():
        logger.warning("LivePortrait source image missing: %s", source)
        return None

    driving = _default_driving_video(repo)
    if driving is None:
        logger.warning("No driving video for LivePortrait (set LIVEPORTRAIT_DRIVING_VIDEO)")
        return None

    work = portrait_output_dir(interview_id)
    token = uuid.uuid4().hex[:12]
    wav_path = work / f"{token}.wav"
    raw_out = work / f"{token}_raw"

    loop = asyncio.get_running_loop()

    try:
        await loop.run_in_executor(None, lambda: synthesize_tts_wav(cleaned, wav_path))
        emotion = await loop.run_in_executor(None, lambda: detect_emotion_from_wav(wav_path))

        generated = await loop.run_in_executor(
            None,
            lambda: _run_liveportrait(
                repo,
                source_image=source,
                driving_video=driving,
                output_dir=raw_out,
            ),
        )
        if generated is None:
            return {"emotion": emotion}

        final = work / f"{token}.mp4"
        shutil.move(str(generated), final)
        return {
            "url": media_url_for(final),
            "emotion": emotion,
        }
    except Exception as exc:
        logger.exception("portrait animation failed: %s", exc)
        return None
    finally:
        if wav_path.exists():
            wav_path.unlink(missing_ok=True)
        if raw_out.exists() and raw_out.is_dir():
            shutil.rmtree(raw_out, ignore_errors=True)
