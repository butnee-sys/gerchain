from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.recovery_outbox import OutboxEvent


def deterministic_event_id(event_type: str, transaction_id: str) -> str:
    if not event_type or not transaction_id:
        raise ValueError("event_type and transaction_id are required")
    return f"{event_type.lower()}:{transaction_id}"


def enqueue_in_transaction(
    session: Session,
    *,
    event_id: str,
    event_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
) -> bool:
    """Insert an outbox event into the caller's transaction.

    This function never opens a session and never commits. The surrounding
    transaction is the atomicity boundary for business state plus event
    intent. Event delivery happens only after commit.
    """
    if not event_id or not event_type or not aggregate_id:
        raise ValueError("event_id, event_type and aggregate_id are required")

    existing = session.execute(
        select(OutboxEvent)
        .where(OutboxEvent.event_id == event_id)
        .with_for_update()
    ).scalar_one_or_none()
    if existing is not None:
        expected = {
            "event_type": existing.event_type,
            "aggregate_id": existing.aggregate_id,
            "payload_json": existing.payload_json,
        }
        actual_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        actual = {
            "event_type": event_type,
            "aggregate_id": aggregate_id,
            "payload_json": actual_payload,
        }
        if expected != actual:
            raise ValueError("outbox event conflict")
        return False

    now = datetime.now(timezone.utc)
    session.add(
        OutboxEvent(
            event_id=event_id,
            event_type=event_type,
            aggregate_id=aggregate_id,
            payload_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
            state="PENDING",
            lease_until=None,
            attempts=0,
            created_at=now,
            updated_at=now,
        )
    )
    return True


__all__ = ["deterministic_event_id", "enqueue_in_transaction"]
