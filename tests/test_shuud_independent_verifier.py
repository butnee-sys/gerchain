from core.hashing import domain_hash
from escrow.engine import EscrowEngine
from shuud.evidence import create_evidence_envelope
from shuud.incident import create_incident
from shuud.independent_verifier import SHUUDIndependentVerifier
from shuud.release import authorize_release
from shuud.shiid import Decision, SHIIDDecision
from shuud.witness import (
    record_evidence_locked,
    record_release_authorized,
    record_shiid_decision,
)
from witness.chain import WitnessChain


def _bundle():
    incident = create_incident("Ulaanbaatar")
    chain = WitnessChain(
        initial_state={"value": 0},
        manifest={"domain": "SHUUD", "incident_id": incident.incident_id},
        witness_id="WITNESS-ROOT-001",
    )
    evidence = create_evidence_envelope(
        incident.incident_id,
        evidence_refs=["photo-1"],
        gps_coordinates="47.9184,106.9177",
        captured_at="2026-09-12T00:00:10+00:00",
        vehicle_identity_refs=["vehicle-a"],
        consent_refs=["consent-a"],
        media_complete=True,
    )
    record_evidence_locked(chain, evidence)
    decision = SHIIDDecision(
        incident_id=incident.incident_id,
        decision=Decision.APPROVE,
        rule_version="SHUUD-POLICY-1",
        reasons=(),
    )
    record_shiid_decision(chain, decision)

    auth = authorize_release(decision, escrow_id="ESC-001")
    record_release_authorized(chain, auth)

    escrow = EscrowEngine(
        escrow_id="ESC-001",
        amount=1_500_000,
        currency="NEF",
        witness_chain=chain,
    )
    escrow.transition("FUNDED", "2026-09-12T00:00:40+00:00", {"source": "sandbox"})
    escrow.transition("LOCKED", "2026-09-12T00:00:45+00:00", {"source": "sandbox"})
    escrow.transition("RELEASED", "2026-09-12T00:01:00+00:00", {"source": "verified"})

    bundle = {
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
    return bundle, incident, evidence


def test_shuud_independent_verifier_accepts_valid_lifecycle():
    bundle, incident, _ = _bundle()
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is True
    assert result.incident_id == incident.incident_id
    assert result.escrow_id == "ESC-001"


def test_shuud_independent_verifier_rejects_tampered_evidence():
    bundle, _, _ = _bundle()
    bundle["entries"][0]["evidence"]["content_hash"] = "tampered"
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_shuud_independent_verifier_rejects_wrong_incident_id():
    bundle, _, _ = _bundle()
    payload = bundle["entries"][0]["event_payload"]
    payload["incident_id"] = "INC-TAMPERED"
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False


def test_shuud_independent_verifier_rejects_non_approved_decision():
    bundle, _, _ = _bundle()
    for entry in bundle["entries"]:
        payload = entry["event_payload"]
        if payload.get("event_type") == "SHIID_DECISION":
            payload["payload"]["decision"] = "REJECT"
            # The event hash must also be stale; this should fail before
            # application-domain approval is trusted.
            break
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_shuud_independent_verifier_rejects_missing_locked_to_released_path():
    bundle, _, _ = _bundle()
    bundle["entries"] = [
        e for e in bundle["entries"]
        if not (
            e["record"]["event_type"] == "ESCROW_TRANSITION"
            and e["event_payload"].get("target_state") == "LOCKED"
        )
    ]
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons
