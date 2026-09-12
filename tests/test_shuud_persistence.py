"""SH-16.1 persistence tests.

These tests verify database-level invariants independently of the FastAPI
process-local locks. They do not authorize or execute money movement.
"""

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

from shuud.persistence import (
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    SHUUDPersistenceBase,
    session_scope,
)


def _engine(tmp_path):
    return create_engine(f"sqlite:///{tmp_path / 'shuud.db'}", future=True)


def test_lifecycle_event_identity_is_unique(tmp_path):
    engine = _engine(tmp_path)
    SHUUDPersistenceBase.metadata.create_all(engine)

    with session_scope(engine) as session:
        session.add(
            SHUUDLifecycleEvent(
                incident_id="INC-001",
                event_id="EV-001",
                event_type="SHUUD_EVIDENCE_LOCKED",
                sequence=1,
                event_hash="HASH-1",
                payload_json="{}",
                evidence_json="{}",
            )
        )
        session.commit()

    with session_scope(engine) as session:
        session.add(
            SHUUDLifecycleEvent(
                incident_id="INC-001",
                event_id="EV-001",
                event_type="SHUUD_EVIDENCE_LOCKED",
                sequence=2,
                event_hash="HASH-2",
                payload_json="{}",
                evidence_json="{}",
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("duplicate lifecycle event was persisted")


def test_lifecycle_sequence_is_unique_per_incident(tmp_path):
    engine = _engine(tmp_path)
    SHUUDPersistenceBase.metadata.create_all(engine)

    with session_scope(engine) as session:
        session.add_all(
            [
                SHUUDLifecycleEvent(
                    incident_id="INC-001",
                    event_id="EV-001",
                    event_type="SHUUD_EVIDENCE_LOCKED",
                    sequence=1,
                    event_hash="HASH-1",
                    payload_json="{}",
                    evidence_json="{}",
                ),
                SHUUDLifecycleEvent(
                    incident_id="INC-001",
                    event_id="EV-002",
                    event_type="SHUUD_SHIID_DECISION",
                    sequence=1,
                    event_hash="HASH-2",
                    payload_json="{}",
                    evidence_json="{}",
                ),
            ]
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("duplicate incident sequence was persisted")


def test_one_incident_has_one_escrow(tmp_path):
    engine = _engine(tmp_path)
    SHUUDPersistenceBase.metadata.create_all(engine)

    with session_scope(engine) as session:
        session.add(
            SHUUDEscrowRecord(
                incident_id="INC-001",
                escrow_id="ESC-001",
                state="LOCKED",
                amount_nef="1500000",
                currency="NEF",
                transition_counter=2,
            )
        )
        session.commit()

    with session_scope(engine) as session:
        session.add(
            SHUUDEscrowRecord(
                incident_id="INC-001",
                escrow_id="ESC-002",
                state="LOCKED",
                amount_nef="1500000",
                currency="NEF",
                transition_counter=2,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("second escrow for one incident was persisted")
