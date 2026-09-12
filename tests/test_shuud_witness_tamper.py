"""Adversarial SHUUD tests for tampered authoritative WitnessChain links."""

from copy import deepcopy

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
    decision = SHIIDDecision(
        incident_id=incident.incident_id,
        decision=Decision.APPROVE,
        rule_version="SHUUD-POLICY-1",
        reasons=("ALL_POLICY_GATES_PASSED",),
        damage_estimate_nef=1_500_000,
    )
    auth = authorize_release(decision, escrow_id="ESC-TAMPER")
    record_evidence_locked(chain, evidence, timestamp="2026-09-12T00:00:15+00:00")
    record_shiid_decision(chain, decision, timestamp="2026-09-12T00:00:20+00:00")
    record_release_authorized(chain, auth, timestamp="2026-09-12T00:00:25+00:00")

    escrow = EscrowEngine(
        escrow_id="ESC-TAMPER",
        amount=1_500_000,
        currency="NEF",
        witness_chain=chain,
    )
    escrow.transition("FUNDED", "2026-09-12T00:00:40+00:00", {"source": "sandbox"})
    escrow.transition("LOCKED", "2026-09-12T00:00:45+00:00", {"source": "sandbox"})
    escrow.transition("RELEASED", "2026-09-12T00:01:00+00:00", {"source": "verified"})

    return {
        "manifest": deepcopy(chain.manifest),
        "manifest_hash": chain.manifest_hash,
        "witness_id": chain.witness_id,
        "initial_state": deepcopy(chain.initial_state),
        "entries": [
            {
                "record": deepcopy(e.record.__dict__),
                "event_payload": deepcopy(e.event_payload),
                "evidence": deepcopy(e.evidence),
            }
            for e in chain.entries
        ],
    }


def _tamper(result, entry_index, record_field, value):
    result = deepcopy(result)
    result["entries"][entry_index]["record"][record_field] = value
    return result


def test_verifier_rejects_tampered_event_hash():
    bundle = _bundle()
    bundle = _tamper(bundle, 0, "event_hash", "FORGED-EVENT-HASH")
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_verifier_rejects_tampered_evidence_hash():
    bundle = _bundle()
    bundle = _tamper(bundle, 0, "evidence_hash", "FORGED-EVIDENCE-HASH")
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_verifier_rejects_tampered_previous_state_hash():
    bundle = _bundle()
    bundle = _tamper(bundle, 3, "previous_state_hash", "FORGED-PREVIOUS-STATE")
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_verifier_rejects_tampered_new_state_hash():
    bundle = _bundle()
    bundle = _tamper(bundle, 5, "new_state_hash", "FORGED-NEW-STATE")
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons
