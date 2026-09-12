"""Durable persistence primitives and schema migration for SHUUD.

The persistence layer stores durable lifecycle facts only. It does not replace
WitnessChain or EscrowEngine: those remain authoritative domain engines.
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


CURRENT_SCHEMA_VERSION = 2
_SCHEMA_MIGRATION_LOCK_KEY = "shuud:schema:migration:v2"
_NON_POSTGRES_SCHEMA_LOCK = Lock()


class SHUUDPersistenceBase(DeclarativeBase):
    pass


class SHUUDSchemaVersion(SHUUDPersistenceBase):
    __tablename__ = "shuud_schema_version"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


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
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class SHUUDEvidenceRecord(SHUUDPersistenceBase):
    __tablename__ = "shuud_evidence"
    __table_args__ = (
        UniqueConstraint("incident_id", name="uq_shuud_evidence_incident"),
        UniqueConstraint("incident_id", "content_hash", name="uq_shuud_evidence_content"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(128), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    witness_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class SHUUDDecisionRecord(SHUUDPersistenceBase):
    __tablename__ = "shuud_decisions"
    __table_args__ = (UniqueConstraint("incident_id", name="uq_shuud_decision_incident"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(128), nullable=False)
    damage_estimate_nef: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_json: Mapped[str] = mapped_column(Text, nullable=False)
    witness_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class SHUUDReleaseAuthorizationRecord(SHUUDPersistenceBase):
    __tablename__ = "shuud_release_authorizations"
    __table_args__ = (
        UniqueConstraint("incident_id", name="uq_shuud_authorization_incident"),
        UniqueConstraint("authorization_hash", name="uq_shuud_authorization_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(128), nullable=False)
    escrow_id: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(128), nullable=False)
    authorization_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    damage_estimate_nef: Mapped[str] = mapped_column(String(64), nullable=False)
    authorization_json: Mapped[str] = mapped_column(Text, nullable=False)
    witness_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
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
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


def create_persistence_engine(url: str):
    """Create an engine; transaction ownership remains with the caller."""
    return create_engine(url, future=True)


def _migrate_schema(bind) -> None:
    """Apply additive, restart-safe migrations on the supplied database bind."""
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "shuud_schema_version" not in tables:
        SHUUDSchemaVersion.__table__.create(bind)
        tables.add("shuud_schema_version")

    if "shuud_publication_outbox" in tables:
        columns = {column["name"] for column in inspector.get_columns("shuud_publication_outbox")}
        if "processing_at" not in columns:
            bind.execute(
                text(
                    "ALTER TABLE shuud_publication_outbox "
                    "ADD COLUMN processing_at TIMESTAMP"
                )
            )

    with Session(bind, expire_on_commit=False) as session:
        with session.begin():
            current = session.query(SHUUDSchemaVersion).order_by(SHUUDSchemaVersion.version.desc()).first()
            if current is None:
                session.add(SHUUDSchemaVersion(version=CURRENT_SCHEMA_VERSION))
            elif current.version < CURRENT_SCHEMA_VERSION:
                session.add(SHUUDSchemaVersion(version=CURRENT_SCHEMA_VERSION))


def initialize_schema(engine) -> None:
    """Create tables and migrate them under the appropriate bootstrap lock."""
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
                {"lock_key": _SCHEMA_MIGRATION_LOCK_KEY},
            )
            SHUUDPersistenceBase.metadata.create_all(connection)
            _migrate_schema(connection)
        return

    # Local/CI dialects have no cross-process production guarantee here. The
    # process-local lock only prevents same-process bootstrap races in tests;
    # production PostgreSQL uses the database advisory lock above.
    with _NON_POSTGRES_SCHEMA_LOCK:
        SHUUDPersistenceBase.metadata.create_all(engine)
        _migrate_schema(engine)


def session_scope(engine):
    """Return a fresh Session for one transaction/worker operation."""
    return Session(engine, expire_on_commit=False)


def persist_evidence(session: Session, *, incident_id: str, content_hash: str,
                     evidence_json: str, witness_event_id: str) -> SHUUDEvidenceRecord:
    record = SHUUDEvidenceRecord(
        incident_id=incident_id, content_hash=content_hash,
        evidence_json=evidence_json, witness_event_id=witness_event_id,
    )
    session.add(record)
    return record


def persist_decision(session: Session, *, incident_id: str, decision: str,
                     rule_version: str, damage_estimate_nef: str,
                     decision_json: str, witness_event_id: str) -> SHUUDDecisionRecord:
    record = SHUUDDecisionRecord(
        incident_id=incident_id, decision=decision, rule_version=rule_version,
        damage_estimate_nef=damage_estimate_nef, decision_json=decision_json,
        witness_event_id=witness_event_id,
    )
    session.add(record)
    return record


def persist_release_authorization(
    session: Session, *, incident_id: str, escrow_id: str,
    rule_version: str, authorization_hash: str, damage_estimate_nef: str,
    authorization_json: str, witness_event_id: str,
) -> SHUUDReleaseAuthorizationRecord:
    record = SHUUDReleaseAuthorizationRecord(
        incident_id=incident_id, escrow_id=escrow_id, rule_version=rule_version,
        authorization_hash=authorization_hash, damage_estimate_nef=damage_estimate_nef,
        authorization_json=authorization_json, witness_event_id=witness_event_id,
    )
    session.add(record)
    return record


def atomic_settlement(engine, *, lifecycle_event: dict, authorization: dict, escrow: dict) -> None:
    """Atomically publish authorization, escrow snapshot and release event.

    This function deliberately performs no WitnessChain append and no
    EscrowEngine transition. Those domain actions must already be authoritative
    and successful before their durable publication is committed here.
    """
    if authorization["incident_id"] != escrow["incident_id"]:
        raise ValueError("escrow snapshot mismatch")
    if authorization["escrow_id"] != escrow["escrow_id"]:
        raise ValueError("escrow snapshot mismatch")
    if authorization["damage_estimate_nef"] != escrow["amount_nef"]:
        raise ValueError("amount mismatch")
    if lifecycle_event["incident_id"] != authorization["incident_id"]:
        raise ValueError("lifecycle incident mismatch")

    with Session(engine, expire_on_commit=False) as session:
        with session.begin():
            session.add(SHUUDReleaseAuthorizationRecord(**authorization))
            session.add(SHUUDEscrowRecord(**escrow))
            session.add(SHUUDLifecycleEvent(**lifecycle_event))


__all__ = [
    "CURRENT_SCHEMA_VERSION", "SHUUDPersistenceBase", "SHUUDSchemaVersion",
    "SHUUDLifecycleEvent", "SHUUDEvidenceRecord", "SHUUDDecisionRecord",
    "SHUUDReleaseAuthorizationRecord", "SHUUDEscrowRecord",
    "create_persistence_engine", "initialize_schema", "session_scope",
    "persist_evidence", "persist_decision", "persist_release_authorization",
    "atomic_settlement",
]
