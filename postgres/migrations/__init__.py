from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import text


def apply_migrations(connection, migration_dir: Path) -> None:
    migration_files = sorted(
        migration_dir.glob("*.sql"),
        key=lambda path: int(path.name.split("_", 1)[0]),
    )
    # PostgreSQL advisory transaction lock serializes concurrent migrators.
    # The lock is transaction-scoped and releases automatically on commit/rollback.
    connection.execute(text("SELECT pg_advisory_xact_lock(hashtext('gerchain:migrations'))"))

    for path in migration_files:
        version = int(path.name.split("_", 1)[0])
        sql = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        if version in applied:
            if applied[version] != checksum:
                raise RuntimeError(f"migration checksum mismatch for version {version}: {path.name}")
            continue
        connection.exec_driver_sql(sql)
        connection.execute(
            text("INSERT INTO schema_version(version, checksum) VALUES (:version, :checksum)"),
            {"version": version, "checksum": checksum},
        )
