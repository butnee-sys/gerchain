from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class OutboxBase(DeclarativeBase):
    pass


class OutboxEvent(OutboxBase):
    __tablename__ = "gerchain_outbox_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@dataclass(frozen=True)
class ClaimedEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    payload_json: str
    attempts: int


class PostgreSQLOutbox:
    """Durable event queue with lease-based crash recovery."""

    def __init__(self, session_factory, lease_seconds: int = 60):
        self.session_factory = session_factory
        self.lease_seconds = lease_seconds

    def enqueue(self, *, event_id: str, event_type: str, aggregate_id: str, payload_json: str) -> None:
        now = datetime.now(timezone.utc)
        with self.session_factory() as session:
            if session.execute(select(OutboxEvent).where(OutboxEvent.event_id == event_id)).scalar_one_or_none():
                return
            session.add(OutboxEvent(event_id=event_id, event_type=event_type, aggregate_id=aggregate_id, payload_json=payload_json, state="PENDING", attempts=0, created_at=now, updated_at=now))
            session.commit()

    def claim(self, limit: int = 100) -> list[ClaimedEvent]:
        now = datetime.now(timezone.utc)
        lease = now + timedelta(seconds=self.lease_seconds)
        with self.session_factory() as session:
            rows = session.execute(
                select(OutboxEvent)
                .where((OutboxEvent.state == "PENDING") | ((OutboxEvent.state == "PROCESSING") & (OutboxEvent.lease_until < now)))
                .order_by(OutboxEvent.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            ).scalars().all()
            claimed = []
            for row in rows:
                row.state = "PROCESSING"
                row.lease_until = lease
                row.attempts += 1
                row.updated_at = now
                claimed.append(ClaimedEvent(row.event_id, row.event_type, row.aggregate_id, row.payload_json, row.attempts))
            session.commit()
            return claimed

    def heartbeat(self, event_id: str) -> bool:
        now = datetime.now(timezone.utc)
        with self.session_factory() as session:
            row = session.execute(select(OutboxEvent).where(OutboxEvent.event_id == event_id).with_for_update()).scalar_one_or_none()
            if row is None or row.state != "PROCESSING":
                return False
            row.lease_until = now + timedelta(seconds=self.lease_seconds)
            row.updated_at = now
            session.commit()
            return True

    def complete(self, event_id: str) -> bool:
        now = datetime.now(timezone.utc)
        with self.session_factory() as session:
            row = session.execute(select(OutboxEvent).where(OutboxEvent.event_id == event_id).with_for_update()).scalar_one_or_none()
            if row is None:
                return False
            row.state = "COMPLETED"
            row.lease_until = None
            row.updated_at = now
            session.commit()
            return True

    def recover_expired(self, limit: int = 100) -> int:
        now = datetime.now(timezone.utc)
        with self.session_factory() as session:
            rows = session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.state == "PROCESSING", OutboxEvent.lease_until < now)
                .with_for_update(skip_locked=True)
                .limit(limit)
            ).scalars().all()
            for row in rows:
                row.state = "PENDING"
                row.lease_until = None
                row.updated_at = now
            session.commit()
            return len(rows)


def initialize_outbox_schema(engine) -> None:
    OutboxBase.metadata.create_all(engine)


__all__ = ["OutboxEvent", "ClaimedEvent", "PostgreSQLOutbox", "initialize_outbox_schema"]
