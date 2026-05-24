# syntax=docker/dockerfile:1.7

# ============================================================================
# Interviewer AI - production image
# ----------------------------------------------------------------------------
# Multi-stage build:
#   - builder:  installs deps into /opt/venv using uv
#   - runtime:  copies /opt/venv + app code into a small image
#
# Default CMD is the FastAPI server. The same image is reused for:
#   - api               (default)
#   - worker            (RQ background jobs)
#   - livekit-agent     (joins LiveKit rooms as the AI interviewer)
# by overriding `command:` in docker-compose.
# ============================================================================

ARG PYTHON_VERSION=3.12
# mediapipe (and a few other ML wheels) only ship linux/amd64 — pin the build
# platform so Apple Silicon hosts emulate via Rosetta instead of failing at
# `uv sync`. Override with `--build-arg BUILDPLATFORM=linux/arm64` if a
# future mediapipe release adds aarch64 wheels.
ARG TARGETPLATFORM=linux/amd64

# ──────────────────────────── builder ──────────────────────────────────────
FROM --platform=${TARGETPLATFORM} python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_COMPILE_BYTECODE=0 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_CONCURRENT_DOWNLOADS=2 \
    CMAKE_BUILD_PARALLEL_LEVEL=1 \
    MAKEFLAGS="-j1"

# System deps for native wheels (opencv/insightface/mediapipe/onnxruntime/audio).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        pkg-config \
        git \
        curl \
        ca-certificates \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
        libsndfile1 \
        ffmpeg \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install python deps first for caching.
COPY pyproject.toml ./
COPY uv.lock* ./

# Install python deps first for caching (split steps so build logs show progress).
RUN uv venv /opt/venv

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# ──────────────────────────── runtime ──────────────────────────────────────
FROM --platform=${TARGETPLATFORM} python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV=/opt/venv \
    APP_ENV=production \
    PORT=8000

# Runtime-only system libs (no toolchain).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
        libsndfile1 \
        ffmpeg \
        ca-certificates \
        curl \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --home /app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app . /app

RUN mkdir -p /app/storage/resumes && chown -R app:app /app \
    && chmod +x /app/scripts/start-api.sh /app/scripts/start-api-and-worker.sh

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/api/v1/health" || exit 1

CMD ["/app/scripts/start-api.sh"]
