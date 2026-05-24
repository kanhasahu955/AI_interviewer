"""Orchestrates face + gaze + audio analysis and emits ProctoringEvents."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.core.config import settings
from app.core.redis_client import get_redis
from app.models.proctoring_event import ProctoringKind, ProctoringSeverity
from app.proctoring.audio import AudioMonitor
from app.proctoring.face import FaceDetector
from app.proctoring.gaze import GazeEstimator
from app.services.interview_service import record_proctor_event

logger = logging.getLogger("app.proctoring.pipeline")


class ProctorPipeline:
    """Per-interview proctoring runtime."""

    def __init__(self, interview_id: int):
        self.interview_id = interview_id
        self.face = FaceDetector()
        self.gaze = GazeEstimator()
        self.audio = AudioMonitor()
        self._face_missing_since: float | None = None
        self._gaze_away_since: float | None = None
        self._silence_since: float | None = None
        self._last_flags: dict[str, float] = {}
        self._debounce_seconds = 4.0
        self._gaze_away_threshold = settings.PROCTOR_GAZE_AWAY_SECONDS
        self._silence_threshold = settings.PROCTOR_SILENCE_SECONDS

    def set_reference_frame(self, frame_bgr: np.ndarray) -> bool:
        return self.face.set_reference(frame_bgr)

    def on_frame(self, frame_bgr: np.ndarray, ts: float) -> None:
        face_info = self.face.analyse(frame_bgr)
        gaze_info = self.gaze.analyse(frame_bgr)

        face_count = face_info.get("faces", -1)
        if face_count == 0:
            if self._face_missing_since is None:
                self._face_missing_since = ts
            elif ts - self._face_missing_since > 2.0:
                self._emit(
                    ProctoringKind.face_missing,
                    ProctoringSeverity.warn,
                    {"seconds": ts - self._face_missing_since},
                )
        else:
            self._face_missing_since = None

        if face_count and face_count > 1:
            self._emit(
                ProctoringKind.multi_face,
                ProctoringSeverity.critical,
                {"faces": face_count},
            )

        identity_score = face_info.get("identity_score")
        if identity_score is not None and identity_score < 0.35:
            self._emit(
                ProctoringKind.identity_mismatch,
                ProctoringSeverity.critical,
                {"similarity": identity_score},
            )

        if gaze_info.get("off_axis"):
            if self._gaze_away_since is None:
                self._gaze_away_since = ts
            elif ts - self._gaze_away_since > self._gaze_away_threshold:
                self._emit(
                    ProctoringKind.gaze_away,
                    ProctoringSeverity.info,
                    {
                        "yaw": gaze_info.get("yaw"),
                        "pitch": gaze_info.get("pitch"),
                        "seconds": ts - self._gaze_away_since,
                    },
                )
                self._gaze_away_since = ts
        else:
            self._gaze_away_since = None

    def on_audio_chunk(self, samples: np.ndarray, sr: int) -> None:
        info = self.audio.on_chunk(samples, sr)
        now = time.monotonic()
        if info["silent"]:
            if self._silence_since is None:
                self._silence_since = now
            elif now - self._silence_since > self._silence_threshold:
                self._emit(
                    ProctoringKind.silence,
                    ProctoringSeverity.info,
                    {"seconds": now - self._silence_since},
                )
                self._silence_since = now
        else:
            self._silence_since = None

        if info["speaker_changed"]:
            self._emit(
                ProctoringKind.speaker_mismatch,
                ProctoringSeverity.warn,
                {"rms": info["rms"]},
            )

    def report_external(
        self,
        kind: ProctoringKind,
        *,
        severity: ProctoringSeverity = ProctoringSeverity.info,
        payload: dict | None = None,
    ) -> None:
        """Allow other components (e.g. browser tab-blur) to emit events too."""
        self._emit(kind, severity, payload or {})

    def _emit(
        self, kind: ProctoringKind, severity: ProctoringSeverity, payload: dict[str, Any]
    ) -> None:
        now = time.monotonic()
        last = self._last_flags.get(kind.value)
        if last is not None and now - last < self._debounce_seconds:
            return
        self._last_flags[kind.value] = now

        try:
            evt = record_proctor_event(
                self.interview_id,
                kind=kind,
                severity=severity,
                payload=payload,
                publish=False,
            )
            self._publish(
                {
                    "id": evt.id,
                    "interview_id": self.interview_id,
                    "kind": kind.value,
                    "severity": severity.value,
                    "ts": evt.ts.isoformat() if evt.ts else datetime.now(timezone.utc).isoformat(),
                    "payload": payload,
                }
            )
        except Exception as exc:
            logger.warning("emit proctor event failed: %s", exc)

    def _publish(self, message: dict) -> None:
        try:
            r = get_redis()
            r.publish(f"proctor:{self.interview_id}", json.dumps(message))
        except Exception as exc:
            logger.debug("redis publish skipped: %s", exc)
