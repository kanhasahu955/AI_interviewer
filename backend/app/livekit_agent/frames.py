"""Subscribe to a candidate's video track and sample frames for proctoring."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable

import numpy as np

from app.core.config import settings

logger = logging.getLogger("app.livekit_agent.frames")


FrameCallback = Callable[[np.ndarray, float], None]


async def consume_video(
    track,
    on_frame: FrameCallback,
    *,
    fps: float | None = None,
) -> None:
    """Iterate frames off a LiveKit VideoTrack, throttled to `fps`.

    `on_frame` receives (HxWx3 BGR ndarray, monotonic_seconds).
    """
    target_fps = fps or settings.PROCTOR_FRAME_SAMPLE_FPS
    min_dt = 1.0 / max(target_fps, 0.1)
    last = 0.0

    try:
        from livekit import rtc
    except Exception as exc:  # noqa: BLE001
        logger.warning("livekit.rtc unavailable, frame sampling disabled: %s", exc)
        return

    video_stream = rtc.VideoStream(track)
    try:
        async for event in video_stream:
            now = time.monotonic()
            if now - last < min_dt:
                continue
            last = now
            frame = event.frame
            if frame.width < 64 or frame.height < 64:
                continue
            try:
                array = _frame_to_ndarray(frame)
            except Exception as exc:
                logger.debug("frame decode failed: %s", exc)
                continue
            try:
                on_frame(array, now)
            except Exception as exc:
                logger.warning("frame callback raised: %s", exc)
    finally:
        try:
            await video_stream.aclose()
        except Exception:
            pass


def _frame_to_ndarray(frame) -> np.ndarray:
    """Convert a LiveKit VideoFrame to a BGR ndarray for OpenCV consumption."""
    import cv2

    try:
        from livekit import rtc

        if hasattr(frame, "convert"):
            converted = frame.convert(rtc.VideoBufferType.BGR24)
            w, h = converted.width, converted.height
            data = bytes(converted.data)
            expected = w * h * 3
            if len(data) >= expected:
                return (
                    np.frombuffer(data, dtype=np.uint8, count=expected)
                    .reshape((h, w, 3))
                    .copy()
                )
    except Exception as exc:
        logger.debug("BGR24 convert failed: %s", exc)

    w, h = frame.width, frame.height
    data = np.frombuffer(bytes(frame.data), dtype=np.uint8)
    rgb_size = h * w * 3
    i420_size = h * w * 3 // 2

    if data.size == rgb_size:
        return data.reshape((h, w, 3)).copy()
    if data.size == h * w * 4:
        return data.reshape((h, w, 4))[:, :, :3].copy()
    # LiveKit often ships I420 (1280×720 → 1382400 bytes)
    if data.size == i420_size:
        yuv = data.reshape((h * 3 // 2, w))
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)

    raise ValueError(f"Unexpected frame buffer size: {data.size} for {w}x{h}")
