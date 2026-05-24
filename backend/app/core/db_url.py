"""Build a SQLAlchemy URL string for the configured DB provider."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote_plus

if TYPE_CHECKING:
    from app.core.config import Settings


def build_database_url(settings: "Settings") -> str:
    provider = settings.DB_PROVIDER.value

    if provider == "mysql":
        user = quote_plus(settings.MYSQL_USER or "")
        pwd = quote_plus(settings.MYSQL_PASSWORD or "")
        host = settings.MYSQL_HOST
        port = settings.MYSQL_PORT
        db = settings.MYSQL_DB
        return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4"

    if provider == "snowflake":
        user = quote_plus(settings.SNOWFLAKE_USER or "")
        pwd = quote_plus(settings.SNOWFLAKE_PASSWORD or "")
        account = settings.SNOWFLAKE_ACCOUNT or ""
        db = settings.SNOWFLAKE_DATABASE or ""
        schema = settings.SNOWFLAKE_SCHEMA or "PUBLIC"
        warehouse = settings.SNOWFLAKE_WAREHOUSE or ""
        role = settings.SNOWFLAKE_ROLE or ""
        params = []
        if warehouse:
            params.append(f"warehouse={warehouse}")
        if role:
            params.append(f"role={role}")
        query = "&".join(params)
        base = f"snowflake://{user}:{pwd}@{account}/{db}/{schema}"
        return f"{base}?{query}" if query else base

    if provider == "databricks":
        host = settings.DATABRICKS_SERVER_HOSTNAME or ""
        http_path = settings.DATABRICKS_HTTP_PATH or ""
        token = settings.DATABRICKS_ACCESS_TOKEN or ""
        catalog = settings.DATABRICKS_CATALOG or "main"
        schema = settings.DATABRICKS_SCHEMA or "default"
        return (
            f"databricks://token:{quote_plus(token)}@{host}"
            f"?http_path={quote_plus(http_path)}&catalog={catalog}&schema={schema}"
        )

    raise ValueError(f"Unsupported DB_PROVIDER: {provider}")
