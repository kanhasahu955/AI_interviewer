"""Snowflake-specific SQL compilation helpers."""

from __future__ import annotations

import re

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.compiler import SQLCompiler
from sqlalchemy.sql.dml import Insert

from app.core.types import is_portable_json

_BIND_PARAM = re.compile(r"%\(\w+\)s")


def _variant_column_keys(table) -> set[str]:
    return {col.key for col in table.c if is_portable_json(col.type)}


@compiles(Insert, "snowflake")
def _compile_insert_snowflake(insert: Insert, compiler: SQLCompiler, **kw) -> str:
    """Snowflake rejects PARSE_JSON inside VALUES; use INSERT ... SELECT instead."""
    variant_keys = _variant_column_keys(insert.table)
    if not variant_keys or insert.select is not None:
        return SQLCompiler.visit_insert(compiler, insert, **kw)

    default_sql = SQLCompiler.visit_insert(compiler, insert, **kw)

    col_match = re.search(r"\(([^)]+)\)\s+VALUES", default_sql, re.IGNORECASE)
    val_match = re.search(r"VALUES\s+\((.+)\)\s*$", default_sql, re.IGNORECASE)
    if not col_match or not val_match:
        return default_sql

    col_names = [c.strip().strip('"') for c in col_match.group(1).split(",")]
    val_exprs = _BIND_PARAM.findall(val_match.group(1))
    if len(col_names) != len(val_exprs):
        return default_sql

    variant_lower = {k.lower() for k in variant_keys}
    select_parts = [
        f"PARSE_JSON({val})" if col.lower() in variant_lower else val
        for col, val in zip(col_names, val_exprs)
    ]
    return (
        default_sql[: val_match.start(0)]
        + " SELECT "
        + ", ".join(select_parts)
        + default_sql[val_match.end(0) :]
    )


def register_snowflake_dml() -> None:
    """Import side-effect: registers Snowflake INSERT compiler via @compiles."""
