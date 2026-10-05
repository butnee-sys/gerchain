from __future__ import annotations

import hashlib
import re
from pathlib import Path

from sqlalchemy import text


_VERSION_RE = re.compile(r"^(\d+)_.*\.sql$")


def apply_migrations(connection, migration_dir: Path) -> None:
    """Apply ordered PostgreSQL migrations exactly once with checksum locking."""
    # Serialize first-boot migration across all PostgreSQL application instances.
    # Transaction-scoped advisory lock is released automatically on commit/rollback.
    connection.execute(text("SELECT pg_advisory_xact_lock(8342719)"))

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
        match = _VERSION_RE.match(path.name)
        assert match is not None
        version = int(match.group(1))
        sql = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

        row = connection.execute(
            text("SELECT checksum FROM schema_version WHERE version = :version"),
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
                "INSERT INTO schema_version(version, checksum) "
                "VALUES (:version, :checksum)"
            ),
            {"version": version, "checksum": checksum},
        )

    connection.commit()


__all__ = ["apply_migrations"]
