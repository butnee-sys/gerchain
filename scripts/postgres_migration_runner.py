"""Compatibility CLI routed through the single canonical PostgreSQL migration chain.

The former per-file runner could publish schema versions independently of the
canonical migration registry. It now accepts a canonical migration file only as
a selector, but applies the entire ordered chain via :mod:`postgres.migrations`.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg

from postgres.migrations import _canonical_migration_files, apply_migrations

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MIGRATION_DIR = REPOSITORY_ROOT / "postgres" / "migrations"


def apply_migration(dsn: str, migration_path: Path) -> str:
    """Compatibility wrapper; always applies the canonical migration chain.

    `migration_path` must identify a member of the canonical migration directory.
    Standalone SQL migrations are rejected to prevent a second schema authority.
    """
    if not dsn or not dsn.startswith(("postgresql://", "postgres://")):
        raise ValueError("PostgreSQL DSN is required")
    selected = migration_path.resolve()
    canonical_dir = CANONICAL_MIGRATION_DIR.resolve()
    if selected.parent != canonical_dir:
        raise ValueError(
            "standalone migration execution is disabled; use postgres/migrations "
            "as the single canonical migration chain"
        )
    files = _canonical_migration_files(canonical_dir)
    if selected not in files:
        raise ValueError(f"not a canonical migration file: {selected.name}")

    with psycopg.connect(dsn) as conn:
        before = {
            int(row[0])
            for row in conn.execute(
                "SELECT version FROM schema_version ORDER BY version"
            ).fetchall()
        } if _schema_version_exists(conn) else set()
        applied = apply_migrations(conn, canonical_dir)
        version = int(selected.name.split("_", 1)[0])
        if version in before and not applied:
            return "already-applied"
        return "applied" if applied else "already-applied"


def _schema_version_exists(conn) -> bool:
    row = conn.execute(
        "SELECT to_regclass('public.schema_version')"
    ).fetchone()
    return row is not None and row[0] is not None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compatibility entrypoint for the canonical PostgreSQL migration chain"
    )
    parser.add_argument("--dsn", default=os.environ.get("GERCHAIN_DATABASE_URL"))
    parser.add_argument(
        "migration",
        type=Path,
        nargs="?",
        default=CANONICAL_MIGRATION_DIR / "001_canonical_production.sql",
        help="optional canonical migration selector; the full chain is applied",
    )
    args = parser.parse_args()
    if not args.dsn:
        parser.error("--dsn or GERCHAIN_DATABASE_URL is required")
    print(f"canonical_migration_dir={CANONICAL_MIGRATION_DIR}")
    print(f"selected_migration={args.migration.name}")
    print(f"result={apply_migration(args.dsn, args.migration)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
