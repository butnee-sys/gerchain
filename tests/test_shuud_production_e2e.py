"""SH-16.9 end-to-end contract for authoritative SHUUD settlement publication.

The test builds the complete lifecycle through the existing SHUUD domain,
WitnessChain and EscrowEngine, independently verifies the bundle, then
publishes only the already-authoritative release facts to durable storage.
"""

import json

from sqlalchemy import select

from shuud.independent_verifier import SHUUDIndependentVerifier
from shuud.persistence import (
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    SHUUDReleaseAuthorizationRecord,
)
from shuud.persistence_adapter import SettlementPublication
from shuud.production import create_production_persistence
from tests.test_shuud_lifecycle_adversarial import _bundle


def test_authoritative_lifecycle_publishes_to_production_storage(tmp_path, monkeypatch):
    bundle = _bundle()
    verification = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert verification.verified is True

    incident_id = bundle["manifest"]["incident_id"]
    auth_entry = next(
        entry
        for entry in bundle["entries"]
        if entry["record"]["event_type"] == "SHUUD_RELEASE_AUTHORIZED"
    )
    release_entry = next(
        entry
        for entry in reversed(bundle["entries"])
        if entry["record"]["event_type"] == "ESCROW_TRANSITION"
        and entry["event_payload"]["new_state"] == "RELEASED"
    )

    auth_payload = auth_entry["event_payload"]["payload"]
    release_payload = release_entry["event_payload"]
    release_record = release_entry["record"]

    publication = SettlementPublication(
        lifecycle_event={
            "incident_id": incident_id,
            "event_id": release_record["event_id"],
            "event_type": release_record["event_type"],
            "sequence": release_record["sequence"],
            "event_hash": release_record["event_hash"],
            "payload_json": json.dumps(release_payload, sort_keys=True),
            "evidence_json": json.dumps(release_entry["evidence"], sort_keys=True),
        },
        authorization={
            "incident_id": incident_id,
            "escrow_id": auth_payload["escrow_id"],
            "rule_version": auth_payload["rule_version"],
            "authorization_hash": auth_payload["authorization_hash"],
            "damage_estimate_nef": str(1_500_000),
            "authorization_json": json.dumps(auth_payload, sort_keys=True),
            "witness_event_id": auth_entry["record"]["event_id"],
        },
        escrow={
            "incident_id": incident_id,
            "escrow_id": release_payload["escrow_id"],
            "state": release_payload["new_state"],
            "amount_nef": str(release_payload["amount"]),
            "currency": release_payload["currency"],
            "transition_counter": release_payload["sequence"],
        },
    )

    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "production")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "sqlalchemy")
    adapter = create_production_persistence(
        database_url=f"sqlite:///{tmp_path / 'shuud-e2e.db'}"
    )
    adapter.publish_settlement(publication)

    with adapter.engine.connect() as connection:
        lifecycle = connection.execute(select(SHUUDLifecycleEvent)).fetchall()
        authorization = connection.execute(
            select(SHUUDReleaseAuthorizationRecord)
        ).fetchall()
        escrow = connection.execute(select(SHUUDEscrowRecord)).fetchall()

    assert len(lifecycle) == 1
    assert len(authorization) == 1
    assert len(escrow) == 1
    assert authorization[0].authorization_hash == auth_payload["authorization_hash"]
    assert escrow[0].state == "RELEASED"
    assert escrow[0].amount_nef == "1500000"
