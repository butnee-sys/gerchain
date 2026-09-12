from shuud.persistence import SHUUDPersistence
from witness.chain import WitnessChain


def _bundle():
    chain = WitnessChain(
        initial_state={"value": 0},
        manifest={"purpose": "SHUUD persistence test", "incident_id": "INC-PERSIST-001"},
        witness_id="WITNESS-ROOT-001",
    )
    chain.append_event(
        event_id="INC-PERSIST-001-1",
        event_type="SHUUD_EVIDENCE_LOCKED",
        timestamp="2026-09-13T00:00:00+00:00",
        payload={
            "domain": "SHUUD",
            "event_type": "SHUUD_EVIDENCE_LOCKED",
            "incident_id": "INC-PERSIST-001",
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


def test_shuud_persistence_round_trip_and_verified_recovery(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'shuud.db'}"
    store = SHUUDPersistence(database_url)
    bundle = _bundle()

    store.save_snapshot("INC-PERSIST-001", {"witness_bundle": bundle})

    loaded = store.load_snapshot("INC-PERSIST-001")
    assert loaded == {"witness_bundle": bundle}

    recovered = store.recover_witness("INC-PERSIST-001")
    assert recovered.witness_id == "WITNESS-ROOT-001"
    assert len(recovered.entries) == 1
    assert recovered.entries[0].event_payload["event_type"] == "SHUUD_EVIDENCE_LOCKED"


def test_shuud_persistence_rejects_tampered_witness_snapshot(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'shuud.db'}"
    store = SHUUDPersistence(database_url)
    bundle = _bundle()
    bundle["entries"][0]["evidence"]["content_hash"] = "tampered"
    store.save_snapshot("INC-PERSIST-001", {"witness_bundle": bundle})

    try:
        store.recover_witness("INC-PERSIST-001")
    except ValueError as exc:
        assert "evidence hash mismatch" in str(exc).lower()
    else:
        raise AssertionError("tampered witness snapshot must be rejected")


def test_shuud_persistence_update_and_delete(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'shuud.db'}"
    store = SHUUDPersistence(database_url)
    store.save_snapshot("INC-PERSIST-001", {"witness_bundle": _bundle()})
    store.save_snapshot("INC-PERSIST-001", {"status": "updated"})

    assert store.load_snapshot("INC-PERSIST-001") == {"status": "updated"}

    store.delete_snapshot("INC-PERSIST-001")
    assert store.load_snapshot("INC-PERSIST-001") is None
