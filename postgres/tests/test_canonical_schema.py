from __future__ import annotations

import os

import psycopg
import pytest

from postgres.migrations import apply_migrations
from pathlib import Path

DATABASE_URL = os.environ.get("GERCHAIN_POSTGRES_DSN")
MIGRATION_DIR = Path(__file__).resolve().parents[1] / "schema"

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_POSTGRES_DSN is not configured",
)


def test_canonical_escrow_schema_migration_is_applied():
    with psycopg.connect(DATABASE_URL) as conn:
        apply_migrations(conn, MIGRATION_DIR)

        columns = {
            row[0]
            for row in conn.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'escrows'
                """
            ).fetchall()
        }
        assert {
            "id",
            "sender_address",
            "receiver_address",
            "amount",
            "state",
            "updated_at",
            "refund_destination",
            "currency",
            "version",
            "created_at",
        } <= columns

        state_constraint = conn.execute(
            """
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'escrows'::regclass
              AND conname = 'escrows_state_check'
            """
        ).fetchone()
        assert state_constraint is not None
        definition = state_constraint[0]
        for state in ("CREATED", "FUNDED", "LOCKED", "RELEASED", "REFUNDED", "CANCELLED"):
            assert state in definition

        versions = {
            int(row[0])
            for row in conn.execute("SELECT version FROM schema_version").fetchall()
        }
        assert {1, 2} <= versions
