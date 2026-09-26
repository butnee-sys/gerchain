from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from postgres.migrations import apply_migrations
from postgres.repository import ConcurrentStateTransition, EscrowRepository

DATABASE_URL = os.environ.get("GERCHAIN_POSTGRES_DSN")
MIGRATION_DIR = Path(__file__).resolve().parents[1] / "schema"

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_POSTGRES_DSN is not configured",
)


@pytest.fixture(autouse=True)
def ensure_schema():
    with connect() as conn:
        apply_migrations(conn, MIGRATION_DIR)


def connect():
    return psycopg.connect(DATABASE_URL)


def reset_db():
    with connect() as conn:
        with conn.transaction():
            conn.execute("TRUNCATE audit_logs, outbox, processed_events, escrows CASCADE")


def seed_escrow(escrow_id="race-1"):
    with connect() as conn:
        with conn.transaction():
            conn.execute(
                """
                INSERT INTO escrows(id, sender_address, receiver_address, amount, state, refund_destination, currency)
                VALUES (%s, 'sender', 'receiver', 100, 'CREATED', 'sender', 'MNT')
                """,
                (escrow_id,),
            )


def test_concurrent_state_transition_has_one_winner():
    reset_db()
    seed_escrow()
    barrier = threading.Barrier(2)

    def worker():
        with connect() as conn:
            barrier.wait()
            repo = EscrowRepository(conn)
            try:
                repo.transition(
                    "race-1", "CREATED", "LOCKED", "worker",
                    uuid4(), {"case": "race"}, uuid4().hex,
                )
                return "won"
            except ConcurrentStateTransition:
                return "lost"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))

    assert sorted(results) == ["lost", "won"]
    with connect() as conn:
        row = conn.execute("SELECT state FROM escrows WHERE id = 'race-1'").fetchone()
        assert row[0] == "LOCKED"
        assert conn.execute("SELECT count(*) FROM audit_logs").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM outbox").fetchone()[0] == 1


def test_transition_rolls_back_audit_and_outbox_on_failure():
    reset_db()
    seed_escrow()
    with connect() as conn:
        repo = EscrowRepository(conn)
        with pytest.raises(Exception):
            repo.transition(
                "race-1", "CREATED", "NOT_A_STATE", "worker",
                uuid4(), {"case": "rollback"}, uuid4().hex,
            )

    with connect() as conn:
        assert conn.execute("SELECT state FROM escrows WHERE id = 'race-1'").fetchone()[0] == "CREATED"
        assert conn.execute("SELECT count(*) FROM audit_logs").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0


def test_skip_locked_allows_only_one_outbox_claim():
    reset_db()
    seed_escrow()
    event_id = uuid4()
    with connect() as conn:
        with conn.transaction():
            conn.execute(
                """
                INSERT INTO outbox(event_id, aggregate_type, aggregate_id, event_type, payload)
                VALUES (%s, 'escrow', 'race-1', 'TEST', '{"x": 1}'::jsonb)
                """,
                (event_id,),
            )

    barrier = threading.Barrier(2)

    def claim():
        with connect() as conn:
            barrier.wait()
            return EscrowRepository(conn).claim_one("worker", lease_seconds=60)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim(), range(2)))

    assert sum(result is not None for result in results) == 1
    assert sum(result[-1] is not None for result in results if result is not None) == 1


def test_expired_lease_is_recovered_and_stale_owner_cannot_complete():
    reset_db()
    seed_escrow()
    event_id = uuid4()
    with connect() as conn:
        with conn.transaction():
            conn.execute(
                """
                INSERT INTO outbox(event_id, aggregate_type, aggregate_id, event_type, payload)
                VALUES (%s, 'escrow', 'race-1', 'TEST', '{"x": 1}'::jsonb)
                """,
                (event_id,),
            )

    with connect() as conn:
        first = EscrowRepository(conn).claim_one("worker-a", lease_seconds=1)
    old_token = first[-1]

    time.sleep(1.2)
    with connect() as conn:
        assert EscrowRepository(conn).recover_expired() == 1
        second = EscrowRepository(conn).claim_one("worker-b", lease_seconds=60)
    new_token = second[-1]
    assert new_token != old_token

    with connect() as conn:
        assert EscrowRepository(conn).mark_processed(event_id, old_token) is False
        assert EscrowRepository(conn).mark_processed(event_id, new_token) is True

    with connect() as conn:
        row = conn.execute("SELECT status FROM outbox WHERE event_id = %s", (event_id,)).fetchone()
        assert row[0] == "PROCESSED"
        assert conn.execute("SELECT count(*) FROM processed_events").fetchone()[0] == 1


def test_migrations_are_serialized_and_checksum_is_stable():
    with connect() as conn:
        conn.execute("DROP TABLE IF EXISTS processed_events, outbox, audit_logs, escrows, schema_version CASCADE")
        conn.commit()

    barrier = threading.Barrier(2)

    def migrate():
        with connect() as conn:
            barrier.wait()
            apply_migrations(conn, MIGRATION_DIR)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: migrate(), range(2)))

    with connect() as conn:
        rows = conn.execute("SELECT version, checksum FROM schema_version ORDER BY version").fetchall()
        assert [row[0] for row in rows] == list(range(1, 9))
        assert all(len(row[1]) == 64 for row in rows)


def test_migration_checksum_mismatch_is_rejected(tmp_path):
    with connect() as conn:
        conn.execute("DROP TABLE IF EXISTS processed_events, outbox, audit_logs, escrows, schema_version CASCADE")
        conn.commit()
        apply_migrations(conn, MIGRATION_DIR)

    migration = tmp_path / "001_modified.sql"
    migration.write_text(
        (MIGRATION_DIR / "001_concurrency.sql").read_text(encoding="utf-8")
        + "\n-- modified after deployment\n",
        encoding="utf-8",
    )

    with connect() as conn:
        with pytest.raises(RuntimeError, match="checksum mismatch"):
            apply_migrations(conn, tmp_path)
