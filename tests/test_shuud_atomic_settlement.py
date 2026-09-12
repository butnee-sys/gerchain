"""SH-16.3 atomic persistence boundary tests.

The transaction helper must make a settlement publication atomic: either the
lifecycle event, authorization and escrow snapshot are all committed, or none
are. It does not execute EscrowEngine money movement.
"""

import pytest
from sqlalchemy import create_engine, select

from shuud.persistence import (
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    SHUUDPersistenceBase,
    SHUUDReleaseAuthorizationRecord,
    atomic_settlement,
)


def _engine(tmp_path):
    return create_engine(f"sqlite:///{tmp_path / 'atomic.db'}", future=True)


def test_atomic_settlement_commits_all_records(tmp_path):
    engine = _engine(tmp_path)
    SHUUDPersistenceBase.metadata.create_all(engine)

    atomic_settlement(
        engine,
        lifecycle_event={
            "incident_id": "INC-001",
            "event_id": "EV-RELEASE",
            "event_type": "ESCROW_RELEASED",
            "sequence": 6,
            "event_hash": "HASH-RELEASE",
            "payload_json": "{}",
            "evidence_json": "{}",
        },
        authorization={
            "incident_id": "INC-001",
            "escrow_id": "ESC-001",
            "rule_version": "SHIID-1",
            "authorization_hash": "AUTH-001",
            "damage_estimate_nef": "1500000",
            "authorization_json": "{}",
            "witness_event_id": "EV-AUTH",
        },
        escrow={
            "incident_id": "INC-001",
            "escrow_id": "ESC-001",
            "state": "RELEASED",
            "amount_nef": "1500000",
            "currency": "NEF",
            "transition_counter": 3,
        },
    )

    with engine.connect() as connection:
        assert connection.execute(select(SHUUDLifecycleEvent)).fetchall()
        assert connection.execute(select(SHUUDReleaseAuthorizationRecord)).fetchall()
        assert connection.execute(select(SHUUDEscrowRecord)).fetchall()


def test_atomic_settlement_rolls_back_every_record_on_failure(tmp_path):
    engine = _engine(tmp_path)
    SHUUDPersistenceBase.metadata.create_all(engine)

    with pytest.raises(ValueError, match="escrow snapshot mismatch"):
        atomic_settlement(
            engine,
            lifecycle_event={
                "incident_id": "INC-001",
                "event_id": "EV-RELEASE",
                "event_type": "ESCROW_RELEASED",
                "sequence": 6,
                "event_hash": "HASH-RELEASE",
                "payload_json": "{}",
                "evidence_json": "{}",
            },
            authorization={
                "incident_id": "INC-001",
                "escrow_id": "ESC-001",
                "rule_version": "SHIID-1",
                "authorization_hash": "AUTH-001",
                "damage_estimate_nef": "1500000",
                "authorization_json": "{}",
                "witness_event_id": "EV-AUTH",
            },
            escrow={
                "incident_id": "INC-001",
                "escrow_id": "ESC-OTHER",
                "state": "RELEASED",
                "amount_nef": "1500000",
                "currency": "NEF",
                "transition_counter": 3,
            },
        )

    with engine.connect() as connection:
        assert connection.execute(select(SHUUDLifecycleEvent)).fetchall() == []
        assert connection.execute(select(SHUUDReleaseAuthorizationRecord)).fetchall() == []
        assert connection.execute(select(SHUUDEscrowRecord)).fetchall() == []


def test_atomic_settlement_rejects_amount_mismatch(tmp_path):
    engine = _engine(tmp_path)
    SHUUDPersistenceBase.metadata.create_all(engine)

    with pytest.raises(ValueError, match="amount mismatch"):
        atomic_settlement(
            engine,
            lifecycle_event={
                "incident_id": "INC-001", "event_id": "EV-RELEASE",
                "event_type": "ESCROW_RELEASED", "sequence": 6,
                "event_hash": "HASH-RELEASE", "payload_json": "{}",
                "evidence_json": "{}",
            },
            authorization={
                "incident_id": "INC-001", "escrow_id": "ESC-001",
                "rule_version": "SHIID-1", "authorization_hash": "AUTH-001",
                "damage_estimate_nef": "1500000", "authorization_json": "{}",
                "witness_event_id": "EV-AUTH",
            },
            escrow={
                "incident_id": "INC-001", "escrow_id": "ESC-001",
                "state": "RELEASED", "amount_nef": "1800000", "currency": "NEF",
                "transition_counter": 3,
            },
        )
