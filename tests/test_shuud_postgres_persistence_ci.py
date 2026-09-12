import os
import uuid

import pytest

from shuud.persistence import SHUUDPersistence
from witness.chain import WitnessChain


POSTGRES_DSN = os.getenv("GERCHAIN_POSTGRES_DSN")
pytestmark = pytest.mark.skipif(
    not POSTGRES_DSN,
    reason="GERCHAIN_POSTGRES_DSN is required for PostgreSQL persistence tests",
)


def _bundle(incident_id: str):
    chain = WitnessChain(
        initial_state={"value": 0},
        manifest={
            "purpose": "SHUUD PostgreSQL persistence test",
            "incident_id": incident_id,
        },
        witness_id="WITNESS-ROOT-001",
    )
    chain.append_event(
        event_id=f"{incident_id}-1",
        event_type="SHUUD_EVIDENCE_LOCKED",
        timestamp="2026-09-13T00:00:00+00:00",
        payload={
            "domain": "SHUUD",
            "event_type": "SHUUD_EVIDENCE_LOCKED",
            "incident_id": incident_id,
            "payload": {"evidence_refs": ["photo-1"]},
        },
        evidence={"content_hash": "evidence-hash"},
    )
    return {
        "manifest": chain.manifest,
        "manifest_hash": chain.manifest_hash,
        "witness_id": chain.witness_id,
        "initial_state": chain.initial_state,
        "entries": [
            {
                "record": e.record.__dict__,
                "event_payload": e.event_payload,
                "evidence": e.evidence,
            }
            for e in chain.entries
        ],
    }


def _store() -> SHUUDPersistence:
    return SHUUDPersistence(POSTGRES_DSN)


def _incident_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def test_postgres_round_trip_and_verified_recovery():
    store = _store()
    incident_id = _incident_id("INC-PG-ROUNDTRIP")
    bundle = _bundle(incident_id)

    store.save_snapshot(incident_id, {"witness_bundle": bundle})

    assert store.load_snapshot(incident_id) == {"witness_bundle": bundle}

    recovered = store.recover_witness(incident_id)
    assert recovered.witness_id == "WITNESS-ROOT-001"
    assert len(recovered.entries) == 1
    assert recovered.entries[0].event_payload["event_type"] == "SHUUD_EVIDENCE_LOCKED"

    store.delete_snapshot(incident_id)


def test_postgres_rejects_tampered_witness_snapshot():
    store = _store()
    incident_id = _incident_id("INC-PG-TAMPER")
    bundle = _bundle(incident_id)
    bundle["entries"][0]["evidence"]["content_hash"] = "tampered"
    store.save_snapshot(incident_id, {"witness_bundle": bundle})

    try:
        store.recover_witness(incident_id)
    except ValueError as exc:
        assert "evidence hash mismatch" in str(exc).lower()
    else:
        raise AssertionError("tampered witness snapshot must be rejected")
    finally:
        store.delete_snapshot(incident_id)


def test_postgres_update_and_delete():
    store = _store()
    incident_id = _incident_id("INC-PG-MUTATION")

    store.save_snapshot(incident_id, {"witness_bundle": _bundle(incident_id)})
    store.save_snapshot(incident_id, {"status": "updated"})

    assert store.load_snapshot(incident_id) == {"status": "updated"}

    store.delete_snapshot(incident_id)
    assert store.load_snapshot(incident_id) is None
