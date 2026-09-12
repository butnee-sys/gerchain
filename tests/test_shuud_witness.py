from witness.chain import WitnessChain

from shuud.evidence import create_evidence_envelope
from shuud.shiid import Decision, SHIIDDecision
from shuud.witness import (
    record_evidence_locked,
    record_shiid_decision,
)


def _witness():
    return WitnessChain(
        initial_state={"value": 0, "sequence_counter": 0},
        manifest={"domain": "SHUUD-SANDBOX", "version": "1"},
        witness_id="SHUUD-WITNESS-001",
    )


def _evidence():
    return create_evidence_envelope(
        "INC-001",
        evidence_refs=["PHOTO-001", "VIDEO-001"],
        gps_coordinates="47.9184,106.9177",
        captured_at="2026-09-12T00:00:00+00:00",
        vehicle_identity_refs=["VIN-A", "VIN-B"],
        consent_refs=["CONSENT-A", "CONSENT-B"],
        media_complete=True,
    )


def test_shuud_evidence_is_recorded_by_existing_witness_chain():
    witness = _witness()
    evidence = _evidence()

    record = record_evidence_locked(
        witness,
        evidence,
        timestamp="2026-09-12T00:00:10+00:00",
    )

    assert record.event_type == "SHUUD_EVIDENCE_LOCKED"
    assert record.evidence_hash
    assert len(witness.entries) == 1
    assert witness.entries[0].event_payload["payload"]["content_hash"] == evidence.content_hash


def test_shiid_decision_is_recorded_without_money_movement():
    witness = _witness()
    decision = SHIIDDecision(
        incident_id="INC-001",
        decision=Decision.APPROVE,
        damage_estimate_mnt=1_500_000,
        rule_version="SHIID-0.2",
        reasons=("ALL_POLICY_GATES_PASSED",),
    )

    record = record_shiid_decision(
        witness,
        decision,
        timestamp="2026-09-12T00:00:20+00:00",
    )

    assert record.event_type == "SHIID_DECISION"
    assert len(witness.entries) == 1
    assert witness.entries[0].event_payload["payload"]["decision"] == "APPROVE"
    assert witness.entries[0].event_payload["payload"]["damage_estimate_mnt"] == 1_500_000
    assert witness.entries[0].event_payload["incident_id"] == "INC-001"
