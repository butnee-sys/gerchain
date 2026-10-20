"""PostgreSQL-only migration re-performance tests.

Set GERCHAIN_TEST_DATABASE_URL to an expendable PostgreSQL database. Every test
uses a unique schema and drops it afterward; no public-schema objects are touched.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from sqlalchemy.engine import make_url

from postgres.migrations import apply_migrations, checksum

DATABASE_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_TEST_DATABASE_URL must point to an expendable PostgreSQL database",
)
MIGRATION_DIR = Path(__file__).resolve().parents[2] / "postgres" / "migrations"


def _schema_url(schema: str) -> str:
    assert DATABASE_URL
    url = make_url(DATABASE_URL)
    options = f"-csearch_path={schema},public"
    return url.update_query_dict({"options": options}).set(drivername="postgresql").render_as_string(
        hide_password=False
    )


def _open_schema(schema: str):
    return psycopg.connect(_schema_url(schema))


def _snapshot_escrow(conn):
    rows = conn.execute(
        """
        SELECT id, sender_address, refund_destination, currency, state,
               receiver_address, amount, condition_desc, updated_at
        FROM escrows ORDER BY id
        """
    ).fetchall()
    return rows


def test_seventeen_migrations_preserve_existing_escrow_truth_and_fill_only_missing_created_at():
    assert DATABASE_URL
    schema = "mig_preserve_" + uuid4().hex[:16]
    admin_url = make_url(DATABASE_URL).set(drivername="postgresql").render_as_string(hide_password=False)
    try:
        with psycopg.connect(admin_url, autocommit=True) as admin:
            admin.execute(f'CREATE SCHEMA "{schema}"')
        with _open_schema(schema) as conn:
            # Legacy shape: canonical metadata columns exist, but created_at and
            # version do not. Their absence is the only migration gap in this fixture.
            conn.execute(
                """
                CREATE TABLE escrows (
                    id TEXT PRIMARY KEY,
                    sender_address TEXT NOT NULL,
                    receiver_address TEXT NOT NULL,
                    amount NUMERIC(38,8) NOT NULL,
                    state TEXT NOT NULL,
                    condition_desc TEXT,
                    refund_destination TEXT,
                    currency VARCHAR(16),
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO escrows
                    (id, sender_address, receiver_address, amount, state,
                     condition_desc, refund_destination, currency, updated_at)
                VALUES
                    ('keep-001', 'sender-A', 'receiver-A', 123.45000000, 'LOCKED',
                     'verified condition', 'refund-A', 'MNT', '2025-01-02T03:04:05Z'),
                    ('keep-002', 'sender-B', 'receiver-B', 8.00000000, 'CREATED',
                     NULL, 'refund-B', 'USD', '2025-03-04T05:06:07Z')
                """
            )
            conn.commit()
            before = _snapshot_escrow(conn)
            assert len(before) == 2

        migration_url = _schema_url(schema)
        with psycopg.connect(migration_url) as conn:
            applied = apply_migrations(conn, MIGRATION_DIR)
            assert applied == tuple(range(1, 18))

        with psycopg.connect(migration_url) as conn:
            after = _snapshot_escrow(conn)
            assert after == before, "existing escrow IDs and business values must remain unchanged"
            columns = {
                row[0]
                for row in conn.execute(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = 'escrows'
                    """,
                    (schema,),
                ).fetchall()
            }
            assert {"created_at", "version"} <= columns
            created = conn.execute(
                "SELECT id, created_at, version FROM escrows ORDER BY id"
            ).fetchall()
            assert created == [
                ("keep-001", before[0][8], 0),
                ("keep-002", before[1][8], 0),
            ]
            versions = conn.execute(
                "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
            ).fetchall()
            assert [row[0] for row in versions] == list(range(1, 18))
            assert len({row[0] for row in versions}) == 17
            assert all(row[1] for row in versions)
            assert all(row[2] is not None for row in versions)
            assert all(
                row[1] == checksum((MIGRATION_DIR / _canonical_name(row[0])).read_text(encoding="utf-8"))
                for row in versions
            )
    finally:
        with psycopg.connect(admin_url, autocommit=True) as admin:
            admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def _canonical_name(version: int) -> str:
    from postgres.migrations import _CANONICAL_FILES

    return _CANONICAL_FILES[version - 1]


def test_two_concurrent_migration_runners_publish_each_version_once_and_stably():
    assert DATABASE_URL
    schema = "mig_race_" + uuid4().hex[:16]
    admin_url = make_url(DATABASE_URL).set(drivername="postgresql").render_as_string(hide_password=False)
    try:
        with psycopg.connect(admin_url, autocommit=True) as admin:
            admin.execute(f'CREATE SCHEMA "{schema}"')

        def run_once():
            with psycopg.connect(_schema_url(schema)) as conn:
                return apply_migrations(conn, MIGRATION_DIR)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: run_once(), range(2)))
        assert sorted(results, key=len) == [(), tuple(range(1, 18))]

        with psycopg.connect(_schema_url(schema)) as conn:
            before = conn.execute(
                "SELECT version, checksum, applied_at, COUNT(*) OVER (PARTITION BY version) "
                "FROM schema_version ORDER BY version"
            ).fetchall()
            assert len(before) == 17
            assert [row[0] for row in before] == list(range(1, 18))
            assert all(row[3] == 1 for row in before)
            assert all(row[1] for row in before)
            assert all(row[2] is not None for row in before)

        # A third run must be a no-op and preserve both checksum and applied_at.
        with psycopg.connect(_schema_url(schema)) as conn:
            assert apply_migrations(conn, MIGRATION_DIR) == ()
        with psycopg.connect(_schema_url(schema)) as conn:
            after = conn.execute(
                "SELECT version, checksum, applied_at, COUNT(*) OVER (PARTITION BY version) "
                "FROM schema_version ORDER BY version"
            ).fetchall()
        assert after == before
    finally:
        with psycopg.connect(admin_url, autocommit=True) as admin:
            admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
