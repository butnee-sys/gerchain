"""Deprecated compatibility entrypoint routed to the canonical migration chain.

This module intentionally does not execute postgres/schema/*.sql directly.
All schema changes must be versioned in postgres/migrations and applied by
postgres.migrations.apply_migrations through scripts.postgres_migration_runner.
"""
from __future__ import annotations

import os
from pathlib import Path

from scripts.postgres_migration_runner import (
    CANONICAL_MIGRATION_DIR,
    apply_migration as _apply_canonical_migration,
)

# Compatibility default: selecting version 001 applies the full canonical chain.
MIGRATION_PATH = CANONICAL_MIGRATION_DIR / "001_canonical_production.sql"


def apply_migration(database_url: str, migration_path: Path = MIGRATION_PATH) -> str:
    """Apply the full canonical chain; reject legacy schema-file execution."""
    selected = Path(migration_path).resolve()
    canonical_dir = CANONICAL_MIGRATION_DIR.resolve()
    if selected.parent != canonical_dir:
        raise ValueError(
            "standalone postgres/schema migration execution is disabled; "
            "use postgres/migrations as the sole canonical migration chain"
        )
    return _apply_canonical_migration(database_url, selected)


def main() -> None:
    database_url = os.environ.get("GERCHAIN_DATABASE_URL", "")
    print(apply_migration(database_url))


if __name__ == "__main__":
    main()
