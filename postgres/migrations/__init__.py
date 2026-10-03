from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import text


def apply_migrations(connection, migration_dir: Path) -> None:
    migration_files = sorted(
        migration_dir.glob("*.sql"),
        key=lambda path: int(path.name.split("_", 1)[0]),
    )

    # Serialize the complete migration lifecycle inside one transaction.
    # The transaction-scoped lock remains held until the final commit, so a
    # waiting migrator cannot observe schema_version before the winner commits.
    lock_key = "gerchain:migrations"
    connection.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
        {"lock_key": lock_key},
    )
    try:
