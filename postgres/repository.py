from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4


class ConcurrentStateTransition(RuntimeError):
    pass


class EscrowRepository:
    """PostgreSQL repository preserving state, audit and outbox atomicity."""

    def __init__(self, conn):
        self.conn = conn

    def transition(
        self,
        escrow_id: str,
        expected_state: str,
        new_state: str,
        actor: str,
        event_id: UUID,
        payload: dict,
        tx_hash: str,
    ) -> None:
        with self.conn.transaction():
            row = self.conn.execute(
                """
                SELECT state FROM escrows
                WHERE id = %s
                FOR UPDATE
                """,
                (escrow_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Unknown escrow: {escrow_id}")
            if row[0] != expected_state:
                raise ConcurrentStateTransition(
                    f"Expected {expected_state}, found {row[0]}"
                )

            updated = self.conn.execute(
                """
                UPDATE escrows
                SET state = %s, updated_at = now()
                WHERE id = %s AND state = %s
                """,
                (new_state, escrow_id, expected_state),
            )
            if updated.rowcount != 1:
                raise ConcurrentStateTransition("State changed concurrently")

            self.conn.execute(
                """
                INSERT INTO audit_logs
                    (escrow_id, previous_state, new_state, actor, tx_hash)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (escrow_id, expected_state, new_state, actor, tx_hash),
            )

            self.conn.execute(
                """
                INSERT INTO outbox
                    (event_id, aggregate_type, aggregate_id, event_type, payload)
                VALUES (%s, 'escrow', %s, 'ESCROW_STATE_CHANGED', %s::jsonb)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (event_id, escrow_id, json.dumps(payload)),
            )

    def claim_one(self, worker_id: str, lease_seconds: int = 60):
        """Atomically claim one event and return its lease token with the event."""
        with self.conn.transaction():
            row = self.conn.execute(
                """
                SELECT id, event_id, aggregate_type, aggregate_id, event_type, payload
                FROM outbox
                WHERE status = 'PENDING'
                  AND available_at <= now()
                ORDER BY id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None

            lease_token = uuid4()
            self.conn.execute(
                """
                UPDATE outbox
                SET status = 'PROCESSING',
                    processing_started_at = now(),
                    lease_until = now() + (%s * interval '1 second'),
                    lease_token = %s,
                    attempts = attempts + 1,
                    last_error = NULL
                WHERE id = %s
                """,
                (lease_seconds, lease_token, row[0]),
            )
            return (*row, lease_token)

    def recover_expired(self, limit: int = 100) -> int:
        """Return expired leases to PENDING; ownership changes on the next claim."""
        with self.conn.transaction():
            result = self.conn.execute(
                """
                WITH expired AS (
                    SELECT id
                    FROM outbox
                    WHERE status = 'PROCESSING'
                      AND lease_until < now()
                    ORDER BY id
                    FOR UPDATE SKIP LOCKED
                    LIMIT %s
                )
                UPDATE outbox o
                SET status = 'PENDING',
                    processing_started_at = NULL,
                    lease_until = NULL,
                    lease_token = NULL,
                    available_at = now()
                FROM expired e
                WHERE o.id = e.id
                RETURNING o.id
                """,
                (limit,),
            )
            return result.rowcount

    def mark_processed(self, event_id: UUID, lease_token: UUID) -> bool:
        """Complete only the current lease owner; stale workers cannot finalize a reclaimed event."""
        with self.conn.transaction():
            owned = self.conn.execute(
                """
                SELECT 1
                FROM outbox
                WHERE event_id = %s
                  AND status = 'PROCESSING'
                  AND lease_token = %s
                FOR UPDATE
                """,
                (event_id, lease_token),
            ).fetchone()
            if owned is None:
                return False

            inserted = self.conn.execute(
                """
                INSERT INTO processed_events(event_id)
                VALUES (%s)
                ON CONFLICT (event_id) DO NOTHING
                RETURNING event_id
                """,
                (event_id,),
            ).fetchone()

            self.conn.execute(
                """
                UPDATE outbox
                SET status = 'PROCESSED',
                    processed_at = now(),
                    lease_until = NULL,
                    lease_token = NULL,
                    processing_started_at = NULL
                WHERE event_id = %s AND status = 'PROCESSING' AND lease_token = %s
                """,
                (event_id, lease_token),
            )
            return inserted is not None
