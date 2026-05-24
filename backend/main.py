"""FastAPI entrypoint for Interviewer AI."""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.connections import log_connection_status
from app.core.database import create_db_and_tables, db_startup_error
from app.core.logging_config import print_startup_banner, setup_logging
from app.core.observability import init_all as init_observability
from app.middlewares.error_handlers import register_exception_handlers
from app.middlewares.request_log import RequestLogMiddleware
from app.middlewares.sentry import init_sentry
from app.routes import (
    auth_route,
    health_route,
    interview_route,
    jd_route,
    media_route,
    proctoring_route,
    report_route,
    resume_route,
    stream_route,
    user_route,
)
from app.websocket.interview_socket import router as interview_ws_router

setup_logging()
logger = logging.getLogger("app.main")

init_sentry()
init_observability()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print_startup_banner()
    app.state.db_error = None
    try:
        create_db_and_tables()
    except Exception as exc:
        app.state.db_error = str(exc)
        logger.error("[red bold]Database startup failed:[/] %s", exc)

    def _log_connections():
        try:
            log_connection_status(probe_live=True)
        except Exception as exc:
            logger.warning("Background connection check failed: %s", exc)

    threading.Thread(target=_log_connections, daemon=True).start()
    yield


OPENAPI_TAGS = [
    {"name": "health", "description": "Liveness + dependency probes."},
    {
        "name": "auth",
        "description": (
            "Signup, login, OTP enrolment / verification. Login returns "
            "`access_token`; paste it into the **Authorize** dialog above."
        ),
    },
    {"name": "users", "description": "Authenticated user profile (`/me`)."},
    {"name": "resumes", "description": "Candidate resume upload and listing."},
    {"name": "jds", "description": "Recruiter job-description CRUD."},
    {
        "name": "interviews",
        "description": (
            "Interview lifecycle: schedule, retrieve, end, fetch turns. "
            "`POST /{id}/token` mints a LiveKit JWT for the candidate to join."
        ),
    },
    {"name": "proctoring", "description": "Proctor event ingest + replay."},
    {"name": "reports", "description": "Final interview report."},
    {"name": "stream", "description": "SSE chat fallback (text-only mode)."},
]

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Real-time AI interview platform: LiveKit AV + LangGraph multi-agent "
        "brain (planner / interviewer / evaluator / reporter) + Pinecone RAG "
        "over resume & JD + insightface/mediapipe proctoring.\n\n"
        "**How to authenticate in this page:**\n"
        "1. Use `POST /api/v1/auth/signup` (or `/login`) to obtain an "
        "`access_token`.\n"
        "2. Click **Authorize** (top right), paste the token, and submit.\n"
        "3. The lock icon on every protected endpoint will turn black; "
        "Swagger now sends `Authorization: Bearer <token>` with every request."
    ),
    openapi_tags=OPENAPI_TAGS,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
    },
    lifespan=lifespan,
)

# Order matters: RequestLogMiddleware must run first so every error handler
# below (and every route) sees `request.state.request_id`.
app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

register_exception_handlers(app)


app.include_router(health_route.router, prefix="/api/v1")
app.include_router(auth_route.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(user_route.router, prefix="/api/v1/users", tags=["users"])
app.include_router(resume_route.router, prefix="/api/v1/resumes", tags=["resumes"])
app.include_router(jd_route.router, prefix="/api/v1/jds", tags=["jds"])
app.include_router(
    interview_route.router, prefix="/api/v1/interviews", tags=["interviews"]
)
app.include_router(
    proctoring_route.router,
    prefix="/api/v1/proctoring",
    tags=["proctoring"],
)
app.include_router(report_route.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(stream_route.router, prefix="/api/v1/stream", tags=["stream"])
app.include_router(media_route.router, prefix="/api/v1", tags=["media"])
app.include_router(interview_ws_router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "db_provider": settings.DB_PROVIDER.value,
        "db_error": db_startup_error,
        "docs": "/docs",
    }
