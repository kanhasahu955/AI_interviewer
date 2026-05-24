"""Reusable created/updated timestamps for table models."""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin(SQLModel):
    """Mixin providing UTC `created_at` / `updated_at` columns.

    We avoid passing a shared `Column` instance via `sa_column`; instead we use
    `sa_type` + `sa_column_kwargs` so SQLAlchemy builds a fresh Column per table.
    """

    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": False},
    )
    updated_at: datetime = Field(
        default_factory=_utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": False, "onupdate": _utc_now},
    )
