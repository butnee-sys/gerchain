"""Recoverable durable publication boundary for SHUUD settlement facts.

The outbox is a delivery mechanism, not an authority. WitnessChain and
EscrowEngine remain authoritative. A pending row contains only facts that have
already been produced by those authoritative domain components.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .persistence import (
    SHUUDPersistenceBase,
    SHUUDReleaseAuthorizationRecord,
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    atomic_settlement,
)


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
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def queue_publication(engine, *, publication_key: str, lifecycle_event: dict, authorization: dict, escrow: dict) -> bool:
    """Queue already-authoritative facts for durable delivery.

    Returns True when a new row is created and False when the same publication
    key was already queued. The queue itself never creates or changes domain
    state.
    """
    if not publication_key.strip():
        raise ValueError("publication_key is required")

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


def publish_pending(engine, *, limit: int = 100) -> int:
    """Retry pending publications without replaying domain authority.

    A crash after durable settlement commit but before outbox acknowledgement is
    safe: the unique durable records are recognized as the same publication and
    the outbox row is then marked PUBLISHED. A conflicting durable record is
    treated as a failure rather than overwritten.
    """
    if limit < 1:
        raise ValueError("limit must be positive")

    with Session(engine, expire_on_commit=False) as session:
        rows = session.scalars(
            select(SHUUDPublicationOutbox)
            .where(SHUUDPublicationOutbox.status == "PENDING")
            .order_by(SHUUDPublicationOutbox.id)
            .limit(limit)
        ).all()

    published = 0
    for row in rows:
        lifecycle_event = json.loads(row.lifecycle_event_json)
        authorization = json.loads(row.authorization_json)
        escrow = json.loads(row.escrow_json)
        try:
            with Session(engine, expire_on_commit=False) as session:
                with session.begin():
                    row_locked = session.get(SHUUDPublicationOutbox, row.id)
                    if row_locked is None or row_locked.status != "PENDING":
                        continue
                    row_locked.attempts += 1

            atomic_settlement(
                engine,
                lifecycle_event=lifecycle_event,
                authorization=authorization,
                escrow=escrow,
            )
        except IntegrityError:
            with Session(engine, expire_on_commit=False) as session:
                if not _settlement_exists_exact(
                    session,
                    lifecycle_event=lifecycle_event,
                    authorization=authorization,
                    escrow=escrow,
                ):
                    with session.begin():
                        failed = session.get(SHUUDPublicationOutbox, row.id)
                        if failed is not None:
                            failed.status = "FAILED"
                            failed.last_error = "conflicting durable settlement record"
                    continue
        except Exception as exc:
            with Session(engine, expire_on_commit=False) as session:
                with session.begin():
                    failed = session.get(SHUUDPublicationOutbox, row.id)
                    if failed is not None:
                        failed.status = "PENDING"
                        failed.last_error = str(exc)
            continue

        with Session(engine, expire_on_commit=False) as session:
            with session.begin():
                done = session.get(SHUUDPublicationOutbox, row.id)
                if done is not None:
                    done.status = "PUBLISHED"
                    done.last_error = None
                    done.published_at = datetime.now(timezone.utc)
                    published += 1

    return published


__all__ = ["SHUUDPublicationOutbox", "queue_publication", "publish_pending"]
