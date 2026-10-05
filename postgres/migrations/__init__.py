from __future__ import annotations

from pathlib import Path
import hashlib
import re

from sqlalchemy import text

_VERSION_RE = re.compile(r"^(\d+)_.*\.sql$")
_LOCK_KEY = 8342719


def _execute(connection, sql: str, params: dict | None = None):
    """Execute against either SQLAlchemy Connection or psycopg Connection."""
    if hasattr(connection, "exec_driver_sql"):
        return connection.exec_driver_sql(
            sql,
            params,
            execution_options={"no_parameters": True} if params is None else {},
        )
    if params:
        # Migration parameters are restricted to integer version and SHA-256 hex.
        sql = sql.replace(":version", "%s").replace(":checksum", "%s")
        ordered = [params["version"], params["checksum"]]
        return connection.execute(sql, ordered)
    return connection.execute(sql)



def apply_migrations(connection, migration_dir: Path) -> None:
    """Apply ordered PostgreSQL migrations exactly once with checksum locking."""
    _execute(connection, "SELECT pg_advisory_xact_lock(8342719)")
    try:
        _execute(
            connection,
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "version BIGINT PRIMARY KEY, "
            "checksum TEXT NOT NULL, "
            "applied_at TIMESTAMPTZ NOT NULL DEFAULT now()"
            ")",
        )

        files = sorted(
            p for p in migration_dir.glob("*.sql")
            if _VERSION_RE.match(p.name)
        )

        for path in files:
            version = int(_VERSION_RE.match(path.name).group(1))
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

            if hasattr(connection, "exec_driver_sql"):
                row = connection.execute(
                    text("SELECT checksum FROM schema_version WHERE version = :version"),
                    {"version": version},
                ).scalar_one_or_none()
            else:
                row = connection.execute(
                    "SELECT checksum FROM schema_version WHERE version = %s",
                    (version,),
                ).fetchone()
                row = row[0] if row else None

            if row is not None:
                if row != checksum:
                    raise RuntimeError(
                        f"migration checksum mismatch for version {version}: "
                        f"database={row} file={checksum}"
                    )
                continue

            if hasattr(connection, "exec_driver_sql"):
                connection.exec_driver_sql(
                    sql,
                    execution_options={"no_parameters": True},
                )
                connection.execute(
                    text("INSERT INTO schema_version(version, checksum) VALUES (:version, :checksum)"),
                    {"version": version, "checksum": checksum},
                )
            else:
                connection.execute(sql)
                connection.execute(
                    "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                    (version, checksum),
                )

        connection.commit()
    finally:
        if hasattr(connection, "rollback"):
            connection.rollback()
