"""Simple silence / speaker-change detector for proctoring."""

from __future__ import annotations

import logging
from collections import deque

import numpy as np

logger = logging.getLogger("app.proctoring.audio")


class AudioMonitor:
    """Tracks rolling RMS and reports prolonged silence + speaker changes."""

    def __init__(self, silence_rms: float = 0.005, change_threshold: float = 0.35):
        self._reference_centroid: float | None = None
        self._recent_rms: deque[float] = deque(maxlen=200)
        self.silence_rms = silence_rms
        self.change_threshold = change_threshold

    def on_chunk(self, samples: np.ndarray, sr: int) -> dict:
        if samples.size == 0:
            return {"rms": 0.0, "silent": True, "speaker_changed": False}

        rms = float(np.sqrt(np.mean(samples.astype("float32") ** 2)))
        self._recent_rms.append(rms)
        silent = rms < self.silence_rms

        centroid = _spectral_centroid(samples, sr)
        speaker_changed = False
        if not silent and centroid is not None:
            if self._reference_centroid is None:
                self._reference_centroid = centroid
            else:
                diff = abs(centroid - self._reference_centroid) / max(self._reference_centroid, 1.0)
                if diff > self.change_threshold:
                    speaker_changed = True
                self._reference_centroid = 0.7 * self._reference_centroid + 0.3 * centroid

        return {"rms": rms, "silent": silent, "speaker_changed": speaker_changed}


def _spectral_centroid(samples: np.ndarray, sr: int) -> float | None:
    if samples.size < 256:
        return None
    s = samples.astype("float32")
    if s.max() > 1.0:
        s = s / 32768.0
    spectrum = np.abs(np.fft.rfft(s * np.hanning(len(s))))
    freqs = np.fft.rfftfreq(len(s), 1.0 / sr)
    total = spectrum.sum()
    if total <= 0:
        return None
    return float((spectrum * freqs).sum() / total)
