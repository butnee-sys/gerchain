"""Failure-consistency tests for SHUUD durable settlement publication.

These tests verify that durable publication is atomic and that a failed
publication does not leave a partial settlement record behind. They do not
make persistence authoritative over WitnessChain or EscrowEngine.
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError

from shuud.persistence import (
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    SHUUDReleaseAuthorizationRecord,
    atomic_settlement,
    initialize_schema,
)


def _records(engine):
    with engine.connect() as connection:
        return {
            "lifecycle": connection.execute(select(SHUUDLifecycleEvent)).fetchall(),
            "authorization": connection.execute(
                select(SHUUDReleaseAuthorizationRecord)
            ).fetchall(),
            "escrow": connection.execute(select(SHUUDEscrowRecord)).fetchall(),
        }


def _valid_payload():
    return {
        "lifecycle_event": {
            "incident_id": "INC-FAIL-001",
            "event_id": "EV-RELEASE",
            "event_type": "ESCROW_RELEASED",
            "sequence": 6,
            "event_hash": "HASH-RELEASE",
            "payload_json": "{}",
            "evidence_json": "{}",
        },
        "authorization": {
            "incident_id": "INC-FAIL-001",
            "escrow_id": "ESC-FAIL-001",
            "rule_version": "SHIID-1",
            "authorization_hash": "AUTH-FAIL-001",
            "damage_estimate_nef": "1500000",
            "authorization_json": "{}",
            "witness_event_id": "EV-AUTH",
        },
        "escrow": {
            "incident_id": "INC-FAIL-001",
            "escrow_id": "ESC-FAIL-001",
            "state": "RELEASED",
            "amount_nef": "1500000",
            "currency": "NEF",
            "transition_counter": 3,
        },
    }


def test_atomic_settlement_failure_leaves_no_partial_records(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'failure.db'}")
    initialize_schema(engine)
    payload = _valid_payload()
    payload["escrow"]["amount_nef"] = "999999"

    with pytest.raises(ValueError, match="amount mismatch"):
        atomic_settlement(engine, **payload)

    records = _records(engine)
    assert records == {"lifecycle": [], "authorization": [], "escrow": []}


def test_atomic_settlement_success_is_all_or_nothing(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'success.db'}")
    initialize_schema(engine)
    atomic_settlement(engine, **_valid_payload())

    records = _records(engine)
    assert len(records["lifecycle"]) == 1
    assert len(records["authorization"]) == 1
    assert len(records["escrow"]) == 1


def test_duplicate_authorization_rolls_back_new_escrow_and_lifecycle(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'duplicate.db'}")
    initialize_schema(engine)
    payload = _valid_payload()
    atomic_settlement(engine, **payload)

    duplicate = _valid_payload()
    duplicate["escrow"]["escrow_id"] = "ESC-FAIL-002"
    duplicate["lifecycle_event"]["event_id"] = "EV-RELEASE-002"

    with pytest.raises(IntegrityError):
        atomic_settlement(engine, **duplicate)

    records = _records(engine)
    assert len(records["lifecycle"]) == 1
    assert len(records["authorization"]) == 1
    assert len(records["escrow"]) == 1
    assert records["escrow"][0].escrow_id == "ESC-FAIL-001"
