from datetime import datetime, timezone

from escrow.engine import EscrowEngine
from shuud.evidence import create_evidence_envelope
from shuud.incident import create_incident
from shuud.policy import GateStatus, PolicyInput
from shuud.release import authorize_release, release_escrow
from shuud.shiid import Decision, decide
from shuud.verify import verify_incident
from shuud.witness import (
    record_evidence_locked,
    record_release_authorized,
    record_shiid_decision,
)
from witness.chain import WitnessChain


def test_shuud_end_to_end_to_escrow_release():
    incident_time = datetime(2026, 9, 12, 0, 0, 0, tzinfo=timezone.utc)
    incident = create_incident(
        "Ulaanbaatar",
        vehicle_a="1234ABC",
        vehicle_b="5678DEF",
        occurred_at=incident_time,
    )

    witness = WitnessChain(
        initial_state={"value": 0},
        manifest={"purpose": "SHUUD sandbox E2E"},
        witness_id="WITNESS-ROOT-001",
    )

    evidence = create_evidence_envelope(
        incident.incident_id,
        evidence_refs=["PHOTO-001", "VIDEO-001"],
        gps_coordinates="47.9184,106.9177",
        captured_at="2026-09-12T00:00:15+00:00",
        vehicle_identity_refs=["VIN-A", "VIN-B"],
        consent_refs=["CONSENT-A", "CONSENT-B"],
        media_complete=True,
    )
    record_evidence_locked(
        witness, evidence, timestamp="2026-09-12T00:00:16+00:00"
    )

    verification = verify_incident(incident, evidence.evidence_refs)
    policy = PolicyInput(
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
    )
    decision = decide(incident, verification, policy=policy)
    assert decision.decision is Decision.APPROVE
    record_shiid_decision(
        witness, decision, timestamp="2026-09-12T00:00:30+00:00"
    )

    authorization = authorize_release(
        decision,
        escrow_id="SHUUD-ESCROW-001",
    )
    record_release_authorized(
        witness, authorization, timestamp="2026-09-12T00:00:35+00:00"
    )

    escrow = EscrowEngine(
        escrow_id="SHUUD-ESCROW-001",
        amount=1_500_000,
        currency="MNT",
        witness_chain=witness,
    )
    escrow.transition("FUNDED", "2026-09-12T00:00:40+00:00", {"incident_id": incident.incident_id})
    escrow.transition("LOCKED", "2026-09-12T00:00:45+00:00", {"incident_id": incident.incident_id})
    release_record = release_escrow(
        escrow,
        authorization,
        timestamp="2026-09-12T00:01:00+00:00",
    )

    assert release_record.previous_state == "LOCKED"
    assert release_record.new_state == "RELEASED"
    assert escrow.get_state()["state"] == "RELEASED"
    assert len(witness.entries) == 6
    assert [entry.record.event_type for entry in witness.entries] == [
        "SHUUD_EVIDENCE_LOCKED",
        "SHIID_DECISION",
        "SHUUD_RELEASE_AUTHORIZED",
        "ESCROW_TRANSITION",
        "ESCROW_TRANSITION",
        "ESCROW_TRANSITION",
    ]
