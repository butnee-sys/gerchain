"""Transactional PostgreSQL SQL migration runner.

Migrations are SQL files named <integer>_<name>.sql. Each migration and its
schema_version record are committed in one PostgreSQL transaction. A
transaction-scoped advisory lock serializes independent processes.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
from pathlib import Path

import psycopg

MIGRATION_NAME = re.compile(r"^(\d+)_.*\.sql$")
LOCK_NAMESPACE = 0x47435243  # "GCRC"


def apply_migration(dsn: str, migration_path: Path) -> str:
    sql_bytes = migration_path.read_bytes()
    match = MIGRATION_NAME.match(migration_path.name)
    if not match:
        raise ValueError(f"invalid migration filename: {migration_path.name}")
    version = int(match.group(1))
    checksum = hashlib.sha256(sql_bytes).hexdigest()
    sql = sql_bytes.decode("utf-8")

    with psycopg.connect(dsn) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                # Transaction-scoped: automatically released on commit/rollback.
                cur.execute("SELECT pg_advisory_xact_lock(%s, %s)", (LOCK_NAMESPACE, 0))
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version BIGINT PRIMARY KEY,
                        checksum TEXT NOT NULL,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                cur.execute(
                    "SELECT checksum FROM schema_version WHERE version = %s FOR UPDATE",
                    (version,),
                )
                existing = cur.fetchone()
                if existing is not None:
                    if existing[0] != checksum:
                        raise RuntimeError(
                            f"migration checksum conflict for version {version}: "
                            f"database={existing[0]} file={checksum}"
                        )
                    return "already-applied"

                # Execute the whole migration within the same transaction.
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                    (version, checksum),
                )
    return "applied"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("GERCHAIN_DATABASE_URL"))
    parser.add_argument("migration", type=Path)
    args = parser.parse_args()
    if not args.dsn:
        parser.error("--dsn or GERCHAIN_DATABASE_URL is required")
    print(f"migration={args.migration.name}")
    print(f"sha256={hashlib.sha256(args.migration.read_bytes()).hexdigest()}")
    print(f"result={apply_migration(args.dsn, args.migration)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
