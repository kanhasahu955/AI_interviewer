"""Face detection + optional identity match via insightface."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("app.proctoring.face")


class FaceDetector:
    """Wraps an insightface FaceAnalysis app and exposes face count / identity."""

    def __init__(self, det_size: tuple[int, int] = (320, 320)):
        self._app = None
        self._reference: np.ndarray | None = None
        self._det_size = det_size

    def _ensure_loaded(self) -> bool:
        if self._app is not None:
            return True
        try:
            from insightface.app import FaceAnalysis  # noqa: WPS433

            app = FaceAnalysis(allowed_modules=["detection", "recognition"])
            app.prepare(ctx_id=0, det_size=self._det_size)
            self._app = app
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("insightface unavailable: %s", exc)
            return False

    def set_reference(self, frame_bgr: np.ndarray) -> bool:
        if not self._ensure_loaded():
            return False
        faces = self._app.get(frame_bgr)
        if not faces:
            return False
        self._reference = faces[0].normed_embedding
        return True

    def analyse(self, frame_bgr: np.ndarray) -> dict[str, Any]:
        if not self._ensure_loaded():
            return {"faces": -1, "identity_score": None}

        faces = self._app.get(frame_bgr)
        result: dict[str, Any] = {"faces": len(faces), "identity_score": None}
        if faces and self._reference is not None:
            emb = faces[0].normed_embedding
            score = float(np.dot(self._reference, emb))
            result["identity_score"] = score
        return result
