"""Gaze direction estimate using mediapipe FaceMesh landmarks."""

from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np

logger = logging.getLogger("app.proctoring.gaze")


class GazeEstimator:
    """Estimates yaw/pitch from FaceMesh landmarks; flags sustained gaze-away."""

    NOSE_TIP = 1
    CHIN = 152
    LEFT_EYE_OUTER = 33
    RIGHT_EYE_OUTER = 263
    LEFT_MOUTH = 61
    RIGHT_MOUTH = 291

    def __init__(self, yaw_threshold_deg: float = 25.0, pitch_threshold_deg: float = 20.0):
        self._mesh = None
        self.yaw_threshold = yaw_threshold_deg
        self.pitch_threshold = pitch_threshold_deg

    def _ensure_loaded(self) -> bool:
        if self._mesh is not None:
            return True
        try:
            import mediapipe as mp  # noqa: WPS433

            self._mp = mp
            self._mesh = mp.solutions.face_mesh.FaceMesh(
                refine_landmarks=True,
                max_num_faces=1,
                min_detection_confidence=0.5,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("mediapipe unavailable: %s", exc)
            return False

    def analyse(self, frame_bgr: np.ndarray) -> dict[str, Any]:
        if not self._ensure_loaded():
            return {"yaw": None, "pitch": None, "off_axis": False}

        rgb = frame_bgr[:, :, ::-1]
        h, w = rgb.shape[:2]
        results = self._mesh.process(rgb)
        if not results.multi_face_landmarks:
            return {"yaw": None, "pitch": None, "off_axis": True}

        lm = results.multi_face_landmarks[0].landmark

        def _xy(idx: int) -> tuple[float, float]:
            return lm[idx].x * w, lm[idx].y * h

        nose = _xy(self.NOSE_TIP)
        chin = _xy(self.CHIN)
        left_eye = _xy(self.LEFT_EYE_OUTER)
        right_eye = _xy(self.RIGHT_EYE_OUTER)

        eye_mid_x = (left_eye[0] + right_eye[0]) / 2
        eye_mid_y = (left_eye[1] + right_eye[1]) / 2
        face_width = max(1e-3, abs(right_eye[0] - left_eye[0]))
        face_height = max(1e-3, abs(chin[1] - eye_mid_y))

        yaw = math.degrees(math.atan2(nose[0] - eye_mid_x, face_width))
        pitch = math.degrees(math.atan2(nose[1] - eye_mid_y, face_height))

        off_axis = abs(yaw) > self.yaw_threshold or abs(pitch) > self.pitch_threshold
        return {"yaw": yaw, "pitch": pitch, "off_axis": off_axis}
