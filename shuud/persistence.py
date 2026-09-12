"""Durable persistence primitives for SHUUD production integration.

This module stores immutable lifecycle facts only. It does not replace
WitnessChain or EscrowEngine: those remain the authoritative domain engines.
The persistence layer exists to provide transaction durability and database-
level uniqueness across multiple application workers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class SHUUDPersistenceBase(DeclarativeBase):
    pass


class SHUUDLifecycleEvent(SHUUDPersistenceBase):
    __tablename__ = "shuud_lifecycle_events"
    __table_args__ = (
        UniqueConstraint("incident_id", "event_id", name="uq_shuud_incident_event"),
        UniqueConstraint("incident_id", "sequence", name="uq_shuud_incident_sequence"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SHUUDEscrowRecord(SHUUDPersistenceBase):
    __tablename__ = "shuud_escrows"
    __table_args__ = (
        UniqueConstraint("escrow_id", name="uq_shuud_escrow_id"),
        UniqueConstraint("incident_id", name="uq_shuud_incident_escrow"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    escrow_id: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_nef: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    transition_counter: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


@dataclass(frozen=True)
class PersistenceConfig:
    url: str


def create_persistence_engine(config: PersistenceConfig):
    """Create an engine; transaction ownership remains with the caller."""
    return create_engine(config.url, future=True)


def initialize_schema(engine) -> None:
    """Create only the SHUUD persistence tables for a new environment."""
    SHUUDPersistenceBase.metadata.create_all(engine)


def session_scope(engine):
    """Return a fresh Session for one transaction/worker operation."""
    return Session(engine, expire_on_commit=False)
