from __future__ import annotations

from datetime import datetime, timezone
import json

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.orm import Session

from persistence.recovery_outbox import OutboxEvent


def enqueue_in_transaction(
    session: Session,
    *,
    event_id: str,
    event_type: str,
    aggregate_id: str,
    payload: dict,
) -> bool:
    """Insert an outbox event into the caller's transaction.

    No session is opened and no commit is performed here. Delivery/claiming
    remains an independent post-commit concern.
    """
    existing = session.execute(
        select(OutboxEvent)
        .where(OutboxEvent.event_id == event_id)
        .with_for_update()
    ).scalar_one_or_none()
    if existing is not None:
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


__all__ = ["enqueue_in_transaction"]
