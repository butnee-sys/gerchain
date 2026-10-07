from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os

import psycopg

from postgres.migrations import apply_migrations


def _dsn() -> str:
    return os.environ.get("GERCHAIN_TEST_DATABASE_URL") or os.environ["GERCHAIN_POSTGRES_DSN"]


def _run_migrations() -> None:
    with psycopg.connect(_dsn()) as conn:
        apply_migrations(
            conn,
            Path(__file__).resolve().parents[1] / "migrations",
        )


def test_migrations_are_serialized_and_checksum_is_stable():
    # EA-35.40: exact fresh PostgreSQL re-performance gate on the current migration runner.
    # Two independent database sessions race the same fresh PostgreSQL database.
    # The migration runner must use a session-scoped advisory lock so a
    # completed publication cannot be duplicated by the competing session.
    # The migration runner must serialize publication and leave exactly one
    # authoritative schema_version row per version.
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_run_migrations) for _ in range(2)]
        for future in futures:
            future.result()

    with psycopg.connect(_dsn()) as conn:
        rows = conn.execute(
            "SELECT version, checksum FROM schema_version ORDER BY version"
        ).fetchall()

    versions = [row[0] for row in rows]
    assert versions == sorted(set(versions))
    assert versions
    assert max(versions) >= 12
    assert all(checksum for _, checksum in rows)

    # A second publication pass must remain idempotent after the concurrent race.
    _run_migrations()
    with psycopg.connect(_dsn()) as conn:
        rows_after = conn.execute(
            "SELECT version, checksum FROM schema_version ORDER BY version"
        ).fetchall()
    assert rows_after == rows
