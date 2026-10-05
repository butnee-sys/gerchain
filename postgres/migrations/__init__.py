from __future__ import annotations

from pathlib import Path
import hashlib
import re

_VERSION_RE = re.compile(r"^(\d+)_.*\.sql$")

from sqlalchemy import text


def apply_migrations(connection, migration_dir: Path) -> None:
    """Apply ordered PostgreSQL migrations exactly once with checksum locking."""
    connection.execute(text("SELECT pg_advisory_xact_lock(8342719)"))

    # Keep production migration history separate from the legacy schema_version
    # table used by older PostgreSQL bootstrap SQL.
    connection.execute(
        text(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "version BIGINT PRIMARY KEY, "
            "checksum TEXT NOT NULL, "
            "applied_at TIMESTAMPTZ NOT NULL DEFAULT now()"
            ")"
        )
    )

    files = sorted(
        p for p in migration_dir.glob("*.sql")
        if _VERSION_RE.match(p.name)
    )

    for path in files:
        version = int(_VERSION_RE.match(path.name).group(1))
        sql = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

        row = connection.execute(
            text(
                "SELECT checksum FROM gerchain_schema_version "
                "WHERE version = :version"
            ),
            {"version": version},
        ).scalar_one_or_none()

        if row is not None:
            if row != checksum:
                raise RuntimeError(
                    f"migration checksum mismatch for version {version}: "
                    f"database={row} file={checksum}"
                )
            continue

        connection.exec_driver_sql(sql)
        connection.execute(
            text(
                "INSERT INTO gerchain_schema_version(version, checksum) "
                "VALUES (:version, :checksum)"
            ),
            {"version": version, "checksum": checksum},
        )

    connection.commit()
