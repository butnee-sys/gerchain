from datetime import datetime, timezone

from escrow.engine import EscrowEngine
from shuud.evidence import create_evidence_envelope
from shuud.incident import create_incident
from shuud.persistence import SHUUDPersistence
from shuud.policy import GateStatus, PolicyInput
from shuud.release import authorize_release
from shuud.runtime_store import SHUUDRuntimeStore
from shuud.shiid import decide
from shuud.verify import verify_incident
from shuud.witness import (
    record_evidence_locked,
    record_shiid_decision,
    record_release_authorized,
)
from witness.chain import WitnessChain


def _runtime(tmp_path):
    persistence = SHUUDPersistence(f"sqlite:///{tmp_path / 'runtime.db'}")
    store = SHUUDRuntimeStore(persistence)

    incident = create_incident(
        "Ulaanbaatar",
        vehicle_a="1234ABC",
        vehicle_b="5678DEF",
        occurred_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
    )
    witness = WitnessChain(
        initial_state={"value": 0, "incident_id": incident.incident_id},
        manifest={"purpose": "SHUUD runtime store", "incident_id": incident.incident_id},
        witness_id="WITNESS-ROOT-001",
    )
    evidence = create_evidence_envelope(
        incident.incident_id,
        evidence_refs=["PHOTO-001"],
        gps_coordinates="47.9184,106.9177",
        captured_at="2026-09-13T00:00:15+00:00",
        vehicle_identity_refs=["VIN-A", "VIN-B"],
        consent_refs=["CONSENT-A", "CONSENT-B"],
        media_complete=True,
    )
    record_evidence_locked(witness, evidence, timestamp=evidence.captured_at)

    decision = decide(
        incident,
        verify_incident(incident, evidence.evidence_refs),
        policy=PolicyInput(
            two_party_consent=GateStatus.PASS,
            vehicle_identity_verified=GateStatus.PASS,
            timestamp_location_verified=GateStatus.PASS,
            media_complete=GateStatus.PASS,
            no_injury=GateStatus.PASS,
            no_third_party_property_damage=GateStatus.PASS,
            damage_estimate_mnt=1_500_000,
            dispute_present=GateStatus.PASS,
            fraud_flag=GateStatus.PASS,
            insurance_valid=GateStatus.PASS,
            beneficiary_valid=GateStatus.PASS,
            witness_verified=GateStatus.PASS,
        ),
    )
    record_shiid_decision(witness, decision, timestamp="2026-09-13T00:00:30+00:00")

    authorization = authorize_release(decision, escrow_id="ESC-RUNTIME-001")
    record_release_authorized(witness, authorization, timestamp="2026-09-13T00:00:35+00:00")

    escrow = EscrowEngine(
        escrow_id="ESC-RUNTIME-001",
        amount=1_500_000,
        currency="MNT",
        witness_chain=witness,
    )
    escrow.transition("FUNDED", "2026-09-13T00:00:40+00:00", {
        "incident_id": incident.incident_id,
        "settlement_provider": "NEF",
    })
    escrow.transition("LOCKED", "2026-09-13T00:00:45+00:00", {
        "incident_id": incident.incident_id,
        "settlement_provider": "NEF",
    })

    return store, incident, witness, evidence, decision, authorization, escrow


def test_runtime_store_round_trip_recovers_all_state(tmp_path):
    store, incident, witness, evidence, decision, authorization, escrow = _runtime(tmp_path)

    store.save(
        incident,
        witness,
        evidence=evidence,
        decision=decision,
        authorization=authorization,
        escrow=escrow,
        settlement_provider="NEF",
    )

    snapshot = store.persistence.load_snapshot(incident.incident_id)
    assert snapshot is not None

    recovered_witness = store.recover_witness(incident.incident_id)
    assert len(recovered_witness.entries) == len(witness.entries)

    recovered_incident = store.recover_incident(snapshot)
    recovered_evidence = store.recover_evidence(snapshot)
    recovered_decision = store.recover_decision(snapshot)
    recovered_authorization = store.recover_authorization(snapshot)
    recovered_escrow = store.recover_escrow(snapshot, recovered_witness)

    assert recovered_incident.incident_id == incident.incident_id
    assert recovered_evidence.content_hash == evidence.content_hash
    assert recovered_decision.damage_estimate_mnt == 1_500_000
    assert recovered_authorization.escrow_id == "ESC-RUNTIME-001"
    assert recovered_escrow.get_state()["state"] == "LOCKED"
    assert recovered_escrow.currency == "MNT"


def test_runtime_store_recovery_rejects_tampered_witness(tmp_path):
    store, incident, witness, evidence, decision, authorization, escrow = _runtime(tmp_path)

    store.save(
        incident,
        witness,
        evidence=evidence,
        decision=decision,
        authorization=authorization,
        escrow=escrow,
    )

    snapshot = store.persistence.load_snapshot(incident.incident_id)
    snapshot["witness_bundle"]["entries"][0]["evidence"]["content_hash"] = "tampered"
    store.persistence.save_snapshot(incident.incident_id, snapshot)

    try:
        store.recover_witness(incident.incident_id)
    except ValueError as exc:
        assert "evidence hash mismatch" in str(exc).lower()
    else:
        raise AssertionError("tampered persisted witness must be rejected")


def test_runtime_store_preserves_mnt_and_nef_semantics(tmp_path):
    store, incident, witness, evidence, decision, authorization, escrow = _runtime(tmp_path)

    store.save(
        incident,
        witness,
        evidence=evidence,
        decision=decision,
        authorization=authorization,
        escrow=escrow,
        settlement_provider="NEF",
    )

    snapshot = store.persistence.load_snapshot(incident.incident_id)
    assert snapshot["decision"]["damage_estimate_mnt"] == 1_500_000
    assert snapshot["escrow"]["currency"] == "MNT"
    assert snapshot["escrow"]["settlement_provider"] == "NEF"
