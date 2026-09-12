from shuud.domain import is_shuud_payload, shuud_event_hash
from shuud.evidence import create_evidence_envelope
from shuud.witness import record_evidence_locked
from witness.chain import WitnessChain


def test_shuud_event_is_explicitly_domain_separated():
    evidence = create_evidence_envelope(
        "INC-DOMAIN-001",
        evidence_refs=["PHOTO-1"],
        gps_coordinates="47.9,106.9",
        captured_at="2026-09-12T00:00:01+00:00",
        vehicle_identity_refs=["VIN-A"],
        consent_refs=["CONSENT-A"],
        media_complete=True,
    )
    witness = WitnessChain(
        initial_state={"value": 0},
        manifest={"purpose": "SHUUD domain test"},
        witness_id="WITNESS-ROOT-001",
    )
    record = record_evidence_locked(
        witness, evidence, timestamp="2026-09-12T00:00:02+00:00"
    )
    payload = witness.entries[0].event_payload

    assert record.event_type == "SHUUD_EVIDENCE_LOCKED"
    assert is_shuud_payload(payload)
    assert payload["event_type"] == "SHUUD_EVIDENCE_LOCKED"
    assert payload["incident_id"] == evidence.incident_id
    assert payload["domain"] == "SHUUD"

    application_hash = shuud_event_hash(
        payload["event_type"],
        payload["incident_id"],
        payload["payload"],
    )
    assert application_hash
    # The application commitment and the full WitnessChain event hash are
    # deliberately different domains; SHUUD must not replace GerChain hashing.
    assert application_hash != record.event_hash


def test_shuud_payload_cannot_be_mistaken_for_escrow_payload():
    evidence = create_evidence_envelope(
        "INC-DOMAIN-002",
        evidence_refs=["PHOTO-2"],
        gps_coordinates="47.9,106.9",
        captured_at="2026-09-12T00:00:01+00:00",
        vehicle_identity_refs=["VIN-B"],
        consent_refs=["CONSENT-B"],
        media_complete=True,
    )
    witness = WitnessChain(
        initial_state={"value": 0},
        manifest={"purpose": "SHUUD domain test"},
        witness_id="WITNESS-ROOT-001",
    )
    record_evidence_locked(
        witness, evidence, timestamp="2026-09-12T00:00:02+00:00"
    )
    payload = witness.entries[0].event_payload

    assert payload["domain"] == "SHUUD"
    assert payload["event_type"] != "ESCROW_TRANSITION"
