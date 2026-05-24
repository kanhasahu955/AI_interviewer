"""SQLAlchemy column types with cross-database compatibility."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class PortableJSON(TypeDecorator):
    """JSON column compatible with Postgres/MySQL JSON and Snowflake VARIANT."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "snowflake":
            try:
                from snowflake.sqlalchemy import VARIANT

                return dialect.type_descriptor(VARIANT())
            except ImportError:
                pass
        return dialect.type_descriptor(JSON())

    def bind_processor(self, dialect):
        # Snowflake VARIANT has no JSON bind processor; always serialize here.
        if dialect.name == "snowflake":

            def process(value: Any | None) -> Any:
                return self.process_bind_param(value, dialect)

            return process
        return super().bind_processor(dialect)

    def result_processor(self, dialect, coltype):
        # Snowflake VARIANT has no JSON result processor (_json_deserializer).
        if dialect.name == "snowflake":

            def process(value: Any | None) -> Any:
                return self.process_result_value(value, dialect)

            return process
        return super().result_processor(dialect, coltype)

    def process_bind_param(self, value: Any | None, dialect) -> Any:
        if value is None:
            return None
        if dialect.name == "snowflake":
            if isinstance(value, str):
                return value
            return json.dumps(value, default=str)
        return value

    def process_result_value(self, value: Any | None, dialect) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            return json.loads(value)
        return value


def is_portable_json(column_type: Any) -> bool:
    """True when *column_type* is (or wraps) PortableJSON."""
    if isinstance(column_type, PortableJSON):
        return True
    impl = getattr(column_type, "impl", None)
    return isinstance(impl, PortableJSON)
