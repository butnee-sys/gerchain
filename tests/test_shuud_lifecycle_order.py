"""Adversarial tests for SHUUD causal lifecycle ordering."""

from escrow.engine import EscrowEngine
from shuud.evidence import create_evidence_envelope
from shuud.incident import create_incident
from shuud.independent_verifier import SHUUDIndependentVerifier
from shuud.release import authorize_release
from shuud.shiid import Decision, SHIIDDecision
from shuud.witness import record_evidence_locked, record_release_authorized, record_shiid_decision
from witness.chain import WitnessChain


def _ordered_bundle(*, authorization_before_decision=False):
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
    auth = authorize_release(decision, escrow_id="ESC-ORDER")

    record_evidence_locked(chain, evidence, timestamp="2026-09-12T00:00:15+00:00")
    if authorization_before_decision:
        record_release_authorized(chain, auth, timestamp="2026-09-12T00:00:20+00:00")
        record_shiid_decision(chain, decision, timestamp="2026-09-12T00:00:25+00:00")
    else:
        record_shiid_decision(chain, decision, timestamp="2026-09-12T00:00:20+00:00")
        record_release_authorized(chain, auth, timestamp="2026-09-12T00:00:25+00:00")

    escrow = EscrowEngine(
        escrow_id="ESC-ORDER",
        amount=1_500_000,
        currency="NEF",
        witness_chain=chain,
    )
    escrow.transition("FUNDED", "2026-09-12T00:00:40+00:00", {"source": "sandbox"})
    escrow.transition("LOCKED", "2026-09-12T00:00:45+00:00", {"source": "sandbox"})
    escrow.transition("RELEASED", "2026-09-12T00:01:00+00:00", {"source": "verified"})

    return {
        "manifest": chain.manifest,
        "manifest_hash": chain.manifest_hash,
        "witness_id": chain.witness_id,
        "initial_state": chain.initial_state,
        "entries": [
            {"record": e.record.__dict__, "event_payload": e.event_payload, "evidence": e.evidence}
            for e in chain.entries
        ],
    }


def test_verifier_accepts_causal_ordered_lifecycle():
    result = SHUUDIndependentVerifier().verify_bundle(_ordered_bundle())
    assert result.verified is True


def test_verifier_rejects_release_authorization_before_decision():
    result = SHUUDIndependentVerifier().verify_bundle(
        _ordered_bundle(authorization_before_decision=True)
    )
    assert result.verified is False
    assert "SHUUD_LIFECYCLE_ORDER_INVALID" in result.reasons
