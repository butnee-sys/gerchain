"""SH-16.2 persistence tests.

These tests verify database-level invariants independently of FastAPI
process-local locks. They do not authorize or execute money movement.
"""

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

from shuud.persistence import (
    SHUUDEscrowRecord,
    SHUUDDecisionRecord,
    SHUUDEvidenceRecord,
    SHUUDLifecycleEvent,
    SHUUDPersistenceBase,
    SHUUDReleaseAuthorizationRecord,
    session_scope,
)


def _engine(tmp_path):
    return create_engine(f"sqlite:///{tmp_path / 'shuud.db'}", future=True)


def _tables(engine):
    SHUUDPersistenceBase.metadata.create_all(engine)


def test_lifecycle_event_identity_is_unique(tmp_path):
    engine = _engine(tmp_path)
    _tables(engine)

    with session_scope(engine) as session:
        session.add(SHUUDLifecycleEvent(
            incident_id="INC-001", event_id="EV-001",
            event_type="SHUUD_EVIDENCE_LOCKED", sequence=1,
            event_hash="HASH-1", payload_json="{}", evidence_json="{}",
        ))
        session.commit()

    with session_scope(engine) as session:
        session.add(SHUUDLifecycleEvent(
            incident_id="INC-001", event_id="EV-001",
            event_type="SHUUD_EVIDENCE_LOCKED", sequence=2,
            event_hash="HASH-2", payload_json="{}", evidence_json="{}",
        ))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("duplicate lifecycle event was persisted")


def test_lifecycle_sequence_is_unique_per_incident(tmp_path):
    engine = _engine(tmp_path)
    _tables(engine)

    with session_scope(engine) as session:
        session.add_all([
            SHUUDLifecycleEvent(
                incident_id="INC-001", event_id="EV-001",
                event_type="SHUUD_EVIDENCE_LOCKED", sequence=1,
                event_hash="HASH-1", payload_json="{}", evidence_json="{}",
            ),
            SHUUDLifecycleEvent(
                incident_id="INC-001", event_id="EV-002",
                event_type="SHUUD_SHIID_DECISION", sequence=1,
                event_hash="HASH-2", payload_json="{}", evidence_json="{}",
            ),
        ])
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("duplicate incident sequence was persisted")


def test_one_incident_has_one_escrow(tmp_path):
    engine = _engine(tmp_path)
    _tables(engine)

    with session_scope(engine) as session:
        session.add(SHUUDEscrowRecord(
            incident_id="INC-001", escrow_id="ESC-001", state="LOCKED",
            amount_nef="1500000", currency="NEF", transition_counter=2,
        ))
        session.commit()

    with session_scope(engine) as session:
        session.add(SHUUDEscrowRecord(
            incident_id="INC-001", escrow_id="ESC-002", state="LOCKED",
            amount_nef="1500000", currency="NEF", transition_counter=2,
        ))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("second escrow for one incident was persisted")


def test_one_incident_has_one_evidence_record(tmp_path):
    engine = _engine(tmp_path)
    _tables(engine)

    with session_scope(engine) as session:
        session.add(SHUUDEvidenceRecord(
            incident_id="INC-001", content_hash="HASH-1",
            evidence_json="{}", witness_event_id="EV-001",
        ))
        session.commit()

    with session_scope(engine) as session:
        session.add(SHUUDEvidenceRecord(
            incident_id="INC-001", content_hash="HASH-2",
            evidence_json="{}", witness_event_id="EV-002",
        ))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("second evidence record was persisted")


def test_one_incident_has_one_decision_record(tmp_path):
    engine = _engine(tmp_path)
    _tables(engine)

    with session_scope(engine) as session:
        session.add(SHUUDDecisionRecord(
            incident_id="INC-001", decision="APPROVE",
            rule_version="SHIID-1", damage_estimate_nef="1500000",
            decision_json="{}", witness_event_id="EV-001",
        ))
        session.commit()

    with session_scope(engine) as session:
        session.add(SHUUDDecisionRecord(
            incident_id="INC-001", decision="APPROVE",
            rule_version="SHIID-1", damage_estimate_nef="1500000",
            decision_json="{}", witness_event_id="EV-002",
        ))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("second decision record was persisted")


def test_one_incident_has_one_release_authorization(tmp_path):
    engine = _engine(tmp_path)
    _tables(engine)

    with session_scope(engine) as session:
        session.add(SHUUDReleaseAuthorizationRecord(
            incident_id="INC-001", escrow_id="ESC-001",
            rule_version="SHIID-1", authorization_hash="AUTH-1",
            damage_estimate_nef="1500000", authorization_json="{}",
            witness_event_id="EV-001",
        ))
        session.commit()

    with session_scope(engine) as session:
        session.add(SHUUDReleaseAuthorizationRecord(
            incident_id="INC-001", escrow_id="ESC-001",
            rule_version="SHIID-1", authorization_hash="AUTH-2",
            damage_estimate_nef="1500000", authorization_json="{}",
            witness_event_id="EV-002",
        ))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("second release authorization was persisted")


def test_authorization_hash_is_globally_unique(tmp_path):
    engine = _engine(tmp_path)
    _tables(engine)

    with session_scope(engine) as session:
        session.add(SHUUDReleaseAuthorizationRecord(
            incident_id="INC-001", escrow_id="ESC-001",
            rule_version="SHIID-1", authorization_hash="AUTH-SAME",
            damage_estimate_nef="1500000", authorization_json="{}",
            witness_event_id="EV-001",
        ))
        session.commit()

    with session_scope(engine) as session:
        session.add(SHUUDReleaseAuthorizationRecord(
            incident_id="INC-002", escrow_id="ESC-002",
            rule_version="SHIID-1", authorization_hash="AUTH-SAME",
            damage_estimate_nef="1500000", authorization_json="{}",
            witness_event_id="EV-002",
        ))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("duplicate authorization hash was persisted")
