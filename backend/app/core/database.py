"""Database engine + session helpers (SQLModel)."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.core.types import is_portable_json

# Snowflake INSERT ... VALUES cannot use PARSE_JSON; register SELECT compiler.
if settings.DB_PROVIDER.value == "snowflake":
    import app.core.snowflake_dml  # noqa: F401

logger = logging.getLogger("app.database")

db_startup_error: str | None = None


def _build_engine() -> Engine:
    # `echo` is decoupled from APP_DEBUG to keep the request/error log clean
    # by default. Opt-in with SQL_ECHO=true when you specifically want to see
    # every SELECT/INSERT in the terminal.
    kwargs: dict = {
        "pool_pre_ping": True,
        "echo": settings.SQL_ECHO,
    }
    if settings.DB_PROVIDER.value == "mysql":
        kwargs.update(pool_size=5, max_overflow=10)
    return create_engine(settings.DATABASE_URL, **kwargs)


try:
    engine: Engine | None = _build_engine()
except Exception as exc:
    engine = None
    db_startup_error = str(exc)
    logger.error("Failed to create DB engine: %s", exc)


def _register_snowflake_json_listeners(db_engine: Engine) -> None:
    """Serialize dict/list PortableJSON fields before Snowflake INSERT/UPDATE.

    Snowflake rejects Python dict binds (255001). bind_expression(PARSE_JSON(...))
    still receives raw dicts from the ORM unless we json.dumps on the instance
    before flush and restore Python objects afterward.
    """

    @event.listens_for(Session, "before_flush")
    def _serialize_portable_json(session, flush_context, instances) -> None:
        if session.connection().dialect.name != "snowflake":
            return
        pending: list[tuple[Any, str, Any]] = session.info.setdefault(
            "_portable_json_restore", []
        )
        for obj in session.new.union(session.dirty):
            state = inspect(obj)
            if not state.mapper:
                continue
            for attr in state.mapper.column_attrs:
                col = attr.columns[0]
                if not is_portable_json(col.type):
                    continue
                value = getattr(obj, attr.key, None)
                if isinstance(value, (dict, list)):
                    pending.append((obj, attr.key, value))
                    setattr(obj, attr.key, json.dumps(value, default=str))

    @event.listens_for(Session, "after_flush")
    def _restore_portable_json(session, flush_context) -> None:
        pending: list[tuple[Any, str, Any]] = session.info.pop(
            "_portable_json_restore", []
        )
        for obj, key, value in pending:
            setattr(obj, key, value)


if engine is not None and engine.dialect.name == "snowflake":
    _register_snowflake_json_listeners(engine)


def create_db_and_tables() -> None:
    """Create database tables from registered SQLModel metadata.

    Snowflake's regular tables do not support indexes (only Snowflake Hybrid
    Tables do), so we drop `Index` objects from the metadata when the dialect
    is Snowflake. Foreign keys are still emitted (Snowflake accepts them
    declaratively, without enforcement).
    """
    global db_startup_error
    if engine is None:
        raise RuntimeError(f"DB engine not initialised: {db_startup_error}")

    # Import models so SQLModel metadata is populated.
    from app import models  # noqa: F401

    dialect = engine.dialect.name
    if dialect == "snowflake":
        _adapt_metadata_for_snowflake()

    SQLModel.metadata.create_all(engine)


def _adapt_metadata_for_snowflake() -> None:
    """Make SQLModel metadata compatible with Snowflake's regular tables.

    Snowflake has three significant divergences from MySQL/Postgres that
    affect a stock SQLModel schema, all handled here at metadata-translation
    time so the *models* stay portable:

    1. **No indexes on regular tables** (only Snowflake Hybrid Tables support
       them). We strip every `Index` object and clear column-level
       `index=True` flags.

    2. **`JSON` columns must be `VARIANT`.** Snowflake's SQLAlchemy dialect
       can't compile the generic `JSON` type, so we swap each `JSON` column
       for `snowflake.sqlalchemy.VARIANT`.

    3. **`AUTOINCREMENT` returns nothing.** snowflake-connector-python doesn't
       surface the generated id via `cursor.lastrowid`, so SQLAlchemy can't
       populate `model.id` after `commit()` and raises *"NULL identity key"*.
       The supported fix is an explicit `Sequence` per table: SQLAlchemy
       fetches `seq.nextval` *before* the INSERT and uses that value, so it
       knows the id without relying on a driver round-trip.
    """
    from sqlalchemy import (
        JSON,
        BigInteger,
        Integer,
        Sequence,
        SmallInteger,
        text,
    )
    from sqlalchemy.schema import ColumnDefault

    def _make_nextval_default(seq_name: str):
        """Return a context-aware default that fetches `<seq>.NEXTVAL`.

        SQLAlchemy's Snowflake dialect doesn't pre-execute attached
        ``Sequence`` objects (``preexecute_autoincrement_sequences`` is False),
        so a bare ``col.default = Sequence(...)`` causes the id column to be
        omitted from the INSERT, which fails on a NOT NULL primary key.

        A context-aware default callable runs inside the same SQLAlchemy
        execution context, on the same connection that's about to issue the
        INSERT, and returns a Python int — exactly what's needed to populate
        the model's ``id`` attribute client-side.
        """

        def _fetch_next_id(ctx) -> int:
            row = ctx.connection.execute(
                text(f"SELECT {seq_name}.NEXTVAL")
            ).scalar()
            return int(row)

        return _fetch_next_id

    sequences_added = 0
    for table in SQLModel.metadata.tables.values():
        # 1) Drop indexes (Snowflake regular tables don't support them).
        if table.indexes:
            for idx in list(table.indexes):
                table.indexes.discard(idx)
        for column in table.columns:
            if getattr(column, "index", False):
                column.index = False

            # 2) JSON -> PortableJSON (Snowflake VARIANT + bind/read helpers).
            from app.core.types import PortableJSON, is_portable_json

            if is_portable_json(column.type):
                continue
            if isinstance(column.type, JSON):
                column.type = PortableJSON()

        # 3) Wire a Sequence + context-aware default on every integer PK.
        pk_cols = list(table.primary_key.columns)
        if len(pk_cols) != 1:
            continue
        pk = pk_cols[0]
        if not isinstance(pk.type, (Integer, BigInteger, SmallInteger)):
            continue

        seq_name = f"{table.name}_id_seq"
        existing_default = pk.default
        if isinstance(existing_default, ColumnDefault) and getattr(
            existing_default, "arg", None
        ) is not None and callable(getattr(existing_default, "arg", None)):
            # already adapted in a previous call
            continue

        # Make sure the sequence object is in metadata so create_all() emits
        # CREATE SEQUENCE for it.
        Sequence(seq_name, metadata=SQLModel.metadata)

        # Wrap the fetcher in ColumnDefault so SQLAlchemy treats it as a
        # context-aware Python-side default.
        column_default = ColumnDefault(_make_nextval_default(seq_name))
        # `Column._set_parent` is how SQLAlchemy associates a default with a
        # column; assigning to `.default` directly bypasses some bookkeeping.
        pk.default = column_default
        column_default._set_parent(pk)

        # Suppress AUTOINCREMENT in the DDL; the sequence + default supply
        # the value, and we need the column to render as plain NUMBER.
        pk.autoincrement = False
        sequences_added += 1

    logger.info(
        "snowflake dialect: %d tables · indexes stripped · JSON->VARIANT · "
        "%d sequences attached for autoincrement",
        len(SQLModel.metadata.tables),
        sequences_added,
    )


def get_db():
    if engine is None:
        raise RuntimeError(f"DB engine not initialised: {db_startup_error}")
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
