"""Application settings for Interviewer AI.

Loads values from the project-root `.env` and exposes a singleton `settings`.
"""

from enum import Enum
from pathlib import Path

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings

AI_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = AI_ROOT / ".env"


class DBProvider(str, Enum):
    mysql = "mysql"
    snowflake = "snowflake"
    databricks = "databricks"


class Settings(BaseSettings):
    APP_NAME: str = "Interviewer AI"

    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    # Comma-separated origins for production CORS, or "*" for dev.
    CORS_ORIGINS: str = "*"
    SQL_ECHO: bool = False  # log every SQL statement (very verbose)

    SECRET_KEY: str = "change-me-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ── OTP / email ───────────────────────────────────────────────────────────
    # OTP_MODE picks the second-factor delivery channel:
    #   - "email" (default): server emails a 6-digit code on login & enrol.
    #   - "totp":  user adds the secret to Google Authenticator / Authy.
    OTP_MODE: str = "email"
    OTP_LENGTH: int = 6
    OTP_TTL_SECONDS: int = 5 * 60

    SMTP_HOST: str | None = None  # e.g. "smtp.gmail.com" (leave blank in dev)
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None  # falls back to SMTP_USER
    SMTP_TLS: bool = True

    DB_PROVIDER: DBProvider = DBProvider.mysql

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DB: str = "interviewer_ai"

    SNOWFLAKE_ACCOUNT: str | None = None
    SNOWFLAKE_USER: str | None = None
    SNOWFLAKE_PASSWORD: str | None = None
    SNOWFLAKE_DATABASE: str | None = None
    SNOWFLAKE_SCHEMA: str = "PUBLIC"
    SNOWFLAKE_WAREHOUSE: str | None = None
    SNOWFLAKE_ROLE: str | None = None
    SNOWFLAKE_REGION: str | None = None
    SNOWFLAKE_CLOUD: str = "aws"
    SNOWFLAKE_HOST: str | None = None
    SNOWFLAKE_LEGACY_LOCATOR: bool = False

    DATABRICKS_SERVER_HOSTNAME: str | None = None
    DATABRICKS_HTTP_PATH: str | None = None
    DATABRICKS_ACCESS_TOKEN: str | None = None
    DATABRICKS_CATALOG: str = "main"
    DATABRICKS_SCHEMA: str = "default"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS_QUEUE: bool = True

    OPENAI_API_KEY: str | None = None
    OPENAI_TTS_MODEL: str = "tts-1"
    OPENAI_TTS_VOICE: str = "alloy"
    OPENAI_STT_MODEL: str = "whisper-1"
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_LANGUAGE: str | None = None

    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"

    GOOGLE_API_KEY: str | None = None
    GOOGLE_MODEL: str = "gemini-1.5-pro"

    HUGGINGFACE_API_KEY: str | None = None
    COHERE_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str | None = None

    SERPER_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None

    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_TRACING: bool = False
    LANGSMITH_PROJECT: str = "interviewer-ai"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_BASE_URL: str = "https://us.cloud.langfuse.com"
    LANGFUSE_HOST: str = "https://us.cloud.langfuse.com"

    PINECONE_API_KEY: str | None = None
    PINECONE_ENV: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "interviewer-ai"
    PINECONE_NAMESPACE: str = "default"

    LIVEKIT_URL: str | None = None
    LIVEKIT_API_KEY: str | None = None
    LIVEKIT_API_SECRET: str | None = None

    # Simli (https://simli.com) — real-time lip-synced talking head in LiveKit room
    SIMLI_ENABLED: bool = False
    SIMLI_API_KEY: str | None = None
    SIMLI_FACE_ID: str | None = None
    SIMLI_AVATAR_IDENTITY: str | None = None  # plugin default: simli-avatar-agent
    SIMLI_AVATAR_NAME: str | None = None

    # LivePortrait (https://liveportrait.org/) — local KwaiVGI/LivePortrait repo + weights
    LIVEPORTRAIT_ENABLED: bool = True
    LIVEPORTRAIT_REPO: str | None = None
    LIVEPORTRAIT_SOURCE_IMAGE: str = "assets/interviewer/alex.jpg"
    LIVEPORTRAIT_DRIVING_VIDEO: str | None = None
    LIVEPORTRAIT_TIMEOUT_SEC: int = 300

    AI_AGENT_MAX_ITERATIONS: int = 20
    AI_AGENT_TIMEOUT: int = 300

    RAG_TOP_K: int = 10
    RAG_SCORE_THRESHOLD: float = 0.7

    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "storage"

    SENTRY_DSN: str | None = None

    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str = "no-reply@interviewer.ai"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    PROCTOR_FRAME_SAMPLE_FPS: float = 2.0
    PROCTOR_GAZE_AWAY_SECONDS: float = 3.0
    PROCTOR_SILENCE_SECONDS: float = 8.0

    @field_validator("DB_PROVIDER", mode="before")
    @classmethod
    def normalize_provider(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def strip_redis_url(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator(
        "USE_REDIS_QUEUE",
        "APP_DEBUG",
        "LANGSMITH_TRACING",
        "SNOWFLAKE_LEGACY_LOCATOR",
        "MAIL_STARTTLS",
        "MAIL_SSL_TLS",
        "LIVEPORTRAIT_ENABLED",
        "SIMLI_ENABLED",
        mode="before",
    )
    @classmethod
    def parse_bool(cls, value):
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return value

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [part.strip() for part in raw.split(",") if part.strip()]

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        from app.core.db_url import build_database_url

        return build_database_url(self)

    @computed_field
    @property
    def STORAGE_DIR(self) -> Path:
        path = Path(self.STORAGE_PATH)
        if not path.is_absolute():
            path = AI_ROOT / path
        return path

    class Config:
        env_file = str(ENV_FILE)
        extra = "ignore"


settings = Settings()


def get_settings() -> Settings:
    return settings
