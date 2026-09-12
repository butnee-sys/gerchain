"""Recoverable durable publication boundary for SHUUD settlement facts.

The outbox is a delivery mechanism, not an authority. WitnessChain and
EscrowEngine remain authoritative. A pending row contains only facts that have
already been produced by those authoritative domain components.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, Integer, String, Text, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .persistence import (
    SHUUDPersistenceBase,
    SHUUDReleaseAuthorizationRecord,
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    atomic_settlement,
)


DEFAULT_CLAIM_TIMEOUT_SECONDS = 300


class SHUUDPublicationOutbox(SHUUDPersistenceBase):
    __tablename__ = "shuud_publication_outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    publication_key: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle_event_json: Mapped[str] = mapped_column(Text, nullable=False)
    authorization_json: Mapped[str] = mapped_column(Text, nullable=False)
    escrow_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    processing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def queue_publication(engine, *, publication_key: str, lifecycle_event: dict, authorization: dict, escrow: dict) -> bool:
    """Queue already-authoritative facts for durable delivery.

    Returns False for a pre-existing key and for a concurrent insert of the
    same key. The queue itself never creates or changes domain state.
    """
    if not publication_key.strip():
        raise ValueError("publication_key is required")

    try:
        with Session(engine, expire_on_commit=False) as session:
            with session.begin():
                existing = session.scalar(
                    select(SHUUDPublicationOutbox).where(
                        SHUUDPublicationOutbox.publication_key == publication_key
                    )
                )
                if existing is not None:
                    return False
                session.add(
                    SHUUDPublicationOutbox(
                        publication_key=publication_key,
                        status="PENDING",
                        lifecycle_event_json=json.dumps(lifecycle_event, sort_keys=True),
                        authorization_json=json.dumps(authorization, sort_keys=True),
                        escrow_json=json.dumps(escrow, sort_keys=True),
                    )
                )
        return True
    except IntegrityError:
        with Session(engine, expire_on_commit=False) as session:
            existing = session.scalar(
                select(SHUUDPublicationOutbox).where(
                    SHUUDPublicationOutbox.publication_key == publication_key
                )
            )
        if existing is not None:
            return False
        raise


def _settlement_exists_exact(session: Session, *, lifecycle_event: dict, authorization: dict, escrow: dict) -> bool:
    auth = session.scalar(
        select(SHUUDReleaseAuthorizationRecord).where(
            SHUUDReleaseAuthorizationRecord.incident_id == authorization["incident_id"]
        )
    )
    esc = session.scalar(
        select(SHUUDEscrowRecord).where(
            SHUUDEscrowRecord.escrow_id == escrow["escrow_id"]
        )
    )
    event = session.scalar(
        select(SHUUDLifecycleEvent).where(
            SHUUDLifecycleEvent.incident_id == lifecycle_event["incident_id"],
            SHUUDLifecycleEvent.event_id == lifecycle_event["event_id"],
        )
    )
    return bool(
        auth is not None
        and esc is not None
        and event is not None
        and auth.authorization_hash == authorization["authorization_hash"]
        and esc.amount_nef == escrow["amount_nef"]
        and esc.state == escrow["state"]
        and event.event_hash == lifecycle_event["event_hash"]
    )


def _mark_failed(engine, row_id: int, message: str) -> None:
    with Session(engine, expire_on_commit=False) as session:
        with session.begin():
            failed = session.get(SHUUDPublicationOutbox, row_id)
            if failed is not None:
                failed.status = "FAILED"
                failed.last_error = message
                failed.processing_at = None


def _claim_pending(engine, row_id: int) -> bool:
    """Atomically claim one PENDING row for a single publication worker."""
    with Session(engine, expire_on_commit=False) as session:
        with session.begin():
            now = datetime.now(timezone.utc)
            result = session.execute(
                update(SHUUDPublicationOutbox)
                .where(
                    SHUUDPublicationOutbox.id == row_id,
                    SHUUDPublicationOutbox.status == "PENDING",
                )
                .values(
                    status="PROCESSING",
                    attempts=SHUUDPublicationOutbox.attempts + 1,
                    processing_at=now,
                )
            )
            return result.rowcount == 1


def _release_claim(engine, row_id: int, *, error: str) -> None:
    with Session(engine, expire_on_commit=False) as session:
        with session.begin():
            row = session.get(SHUUDPublicationOutbox, row_id)
            if row is not None and row.status == "PROCESSING":
                row.status = "PENDING"
                row.last_error = error
                row.processing_at = None


def _recover_stale_claims(engine, *, claim_timeout_seconds: int) -> int:
    """Return abandoned PROCESSING rows to PENDING after a bounded lease."""
    if claim_timeout_seconds < 1:
        raise ValueError("claim_timeout_seconds must be positive")
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=claim_timeout_seconds)
    with Session(engine, expire_on_commit=False) as session:
        with session.begin():
            result = session.execute(
                update(SHUUDPublicationOutbox)
                .where(
                    SHUUDPublicationOutbox.status == "PROCESSING",
                    SHUUDPublicationOutbox.processing_at.is_not(None),
                    SHUUDPublicationOutbox.processing_at < cutoff,
                )
                .values(
                    status="PENDING",
                    processing_at=None,
                    last_error="stale worker claim recovered",
                )
            )
            return result.rowcount


def publish_pending(engine, *, limit: int = 100, claim_timeout_seconds: int = DEFAULT_CLAIM_TIMEOUT_SECONDS) -> int:
    """Retry pending publications without replaying domain authority.

    Claims are leases. A crashed worker leaves PROCESSING behind, and a later
    worker may recover only a claim older than the bounded timeout. Durable
    uniqueness and exact-fact reconciliation remain the final duplicate guard.
    """
    if limit < 1:
        raise ValueError("limit must be positive")
    _recover_stale_claims(engine, claim_timeout_seconds=claim_timeout_seconds)

    with Session(engine, expire_on_commit=False) as session:
        rows = session.scalars(
            select(SHUUDPublicationOutbox)
            .where(SHUUDPublicationOutbox.status == "PENDING")
            .order_by(SHUUDPublicationOutbox.id)
            .limit(limit)
        ).all()

    published = 0
    for row in rows:
        if not _claim_pending(engine, row.id):
            continue

        lifecycle_event = json.loads(row.lifecycle_event_json)
        authorization = json.loads(row.authorization_json)
        escrow = json.loads(row.escrow_json)

        try:
            atomic_settlement(
                engine,
                lifecycle_event=lifecycle_event,
                authorization=authorization,
                escrow=escrow,
            )
        except IntegrityError:
            with Session(engine, expire_on_commit=False) as session:
                exact = _settlement_exists_exact(
                    session,
                    lifecycle_event=lifecycle_event,
                    authorization=authorization,
                    escrow=escrow,
                )
            if not exact:
                _mark_failed(engine, row.id, "conflicting durable settlement record")
                continue
        except Exception as exc:
            _release_claim(engine, row.id, error=str(exc))
            continue

        with Session(engine, expire_on_commit=False) as session:
            with session.begin():
                done = session.get(SHUUDPublicationOutbox, row.id)
                if done is not None and done.status == "PROCESSING":
                    done.status = "PUBLISHED"
                    done.last_error = None
                    done.processing_at = None
                    done.published_at = datetime.now(timezone.utc)
                    published += 1

    return published


__all__ = ["SHUUDPublicationOutbox", "queue_publication", "publish_pending"]
