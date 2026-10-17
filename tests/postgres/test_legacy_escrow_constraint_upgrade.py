"""Real PostgreSQL upgrade proof for legacy escrow state constraints and data preservation."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from postgres.migrations import apply_migrations


def _admin_dsn() -> str:
    value = (
        os.environ.get("GERCHAIN_POSTGRES_DSN")
        or os.environ.get("GERCHAIN_DATABASE_URL")
        or os.environ["GERCHAIN_TEST_DATABASE_URL"]
    )
    return value.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


@pytest.mark.postgres
def test_full_16_migration_chain_repairs_legacy_constraint_without_losing_escrows():
    admin_dsn = _admin_dsn()
    database_name = f"gerchain_legacy_upgrade_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    dsn = make_conninfo(admin_dsn, dbname=database_name)
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "migrations"
    expected_rows = [
        ("legacy-created", "sender-a", "receiver-a", 125, "CREATED", "condition-a"),
        ("legacy-locked", "sender-b", "receiver-b", 900, "LOCKED", "condition-b"),
        ("legacy-released", "sender-c", "receiver-c", 275, "RELEASED", "condition-c"),
    ]
    try:
        with psycopg.connect(dsn) as conn:
            # Reproduce the historical table/constraint before the canonical
            # migration chain runs; rows represent pre-existing production truth.
            conn.execute("""
                CREATE TABLE escrows (
                    id TEXT PRIMARY KEY,
                    sender_address TEXT NOT NULL,
                    receiver_address TEXT NOT NULL,
                    amount NUMERIC(38, 8) NOT NULL CHECK (amount >= 0),
                    currency TEXT NOT NULL DEFAULT 'MNT',
                    state TEXT NOT NULL,
                    condition_desc TEXT,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT legacy_escrow_state_check
                        CHECK (state IN ('CREATED', 'LOCKED', 'RELEASED'))
                )
            """)
            with conn.cursor() as cursor:
                cursor.executemany(
                    """INSERT INTO escrows
                       (id, sender_address, receiver_address, amount, state, condition_desc)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    expected_rows,
                )
            conn.commit()

            apply_migrations(conn, migration_dir)

            actual_rows = conn.execute("""
                SELECT id, sender_address, receiver_address, amount::bigint,
                       state, condition_desc
                FROM escrows ORDER BY id
            """).fetchall()
            assert actual_rows == sorted(expected_rows)

            # Legacy rows without the newly introduced metadata must be
            # backfilled deterministically before NOT NULL hardening.
            metadata_rows = conn.execute(
                "SELECT id, refund_destination, currency FROM escrows ORDER BY id"
            ).fetchall()
            assert metadata_rows == [
                ("legacy-created", "sender-a", "MNT"),
                ("legacy-locked", "sender-b", "MNT"),
                ("legacy-released", "sender-c", "MNT"),
            ]

            versions = conn.execute(
                "SELECT version FROM schema_version ORDER BY version"
            ).fetchall()
            assert [row[0] for row in versions] == list(range(1, 17))

            state_constraints = conn.execute("""
                SELECT conname, pg_get_constraintdef(oid), convalidated
                FROM pg_constraint
                WHERE conrelid = 'escrows'::regclass
                  AND contype = 'c'
                  AND lower(pg_get_constraintdef(oid)) LIKE '%state%'
                ORDER BY conname
            """).fetchall()
            assert len(state_constraints) == 1, state_constraints
            name, definition, validated = state_constraints[0]
            assert name == "escrows_state_canonical_check", state_constraints
            assert validated is True, state_constraints
            assert all(state in definition for state in (
                "CREATED", "FUNDED", "LOCKED", "RELEASED", "REFUNDED", "CANCELLED"
            )), definition

            # Simulate an upgraded installation whose migration ledger is at v15
            # but whose schema drifted after v15 was applied: drop v16's record,
            # replace the canonical state CHECK with a stale legacy CHECK, then
            # prove the new additive migration repairs that already-upgraded DB.
            conn.execute("DELETE FROM schema_version WHERE version = 16")
            conn.execute("ALTER TABLE escrows DROP CONSTRAINT escrows_state_canonical_check")
            conn.execute("""
                ALTER TABLE escrows ADD CONSTRAINT legacy_escrow_state_check
                CHECK (state IN ('CREATED', 'LOCKED', 'RELEASED'))
            """)
            conn.commit()
            apply_migrations(conn, migration_dir)

            # Re-running the entire chain must preserve both data and schema truth.
            apply_migrations(conn, migration_dir)
            rerun_rows = conn.execute("""
                SELECT id, sender_address, receiver_address, amount::bigint,
                       state, condition_desc
                FROM escrows ORDER BY id
            """).fetchall()
            rerun_versions = conn.execute(
                "SELECT version FROM schema_version ORDER BY version"
            ).fetchall()
            assert rerun_rows == actual_rows
            assert [row[0] for row in rerun_versions] == list(range(1, 17))
            assert conn.execute(
                "SELECT COUNT(*) FROM pg_constraint WHERE conrelid='escrows'::regclass "
                "AND conname='legacy_escrow_state_check'"
            ).fetchone()[0] == 0
            conn.commit()
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(database_name)
                )
            )
