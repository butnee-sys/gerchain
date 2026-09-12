"""Adversarial tests for SHUUD authorization and escrow bindings."""

from escrow.engine import EscrowEngine
from shuud.evidence import create_evidence_envelope
from shuud.incident import create_incident
from shuud.independent_verifier import SHUUDIndependentVerifier
from shuud.release import ReleaseAuthorization, authorize_release
from shuud.shiid import Decision, SHIIDDecision
from shuud.witness import (
    record_evidence_locked,
    record_release_authorized,
    record_shiid_decision,
)
from witness.chain import WitnessChain


def _bundle(*, currency="NEF", forged_hash=None, order="normal", include_manifest_incident_id=True):
    incident = create_incident("Ulaanbaatar")
    manifest = {"domain": "SHUUD"}
    if include_manifest_incident_id:
        manifest["incident_id"] = incident.incident_id
    chain = WitnessChain(
        initial_state={"value": 0},
        manifest=manifest,
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
    auth = authorize_release(decision, escrow_id="ESC-BIND")
    if forged_hash is not None:
        auth = ReleaseAuthorization(
            incident_id=auth.incident_id,
            escrow_id=auth.escrow_id,
            rule_version=auth.rule_version,
            authorization_hash=forged_hash,
            damage_estimate_nef=auth.damage_estimate_nef,
        )

    def add_evidence():
        record_evidence_locked(chain, evidence, timestamp="2026-09-12T00:00:15+00:00")

    def add_decision():
        record_shiid_decision(chain, decision, timestamp="2026-09-12T00:00:20+00:00")

    def add_auth():
        record_release_authorized(chain, auth, timestamp="2026-09-12T00:00:25+00:00")

    if order == "auth_before_decision":
        add_evidence()
        add_auth()
        add_decision()
    else:
        add_evidence()
        add_decision()
        add_auth()

    escrow = EscrowEngine(
        escrow_id="ESC-BIND",
        amount=1_500_000,
        currency=currency,
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
            {
                "record": e.record.__dict__,
                "event_payload": e.event_payload,
                "evidence": e.evidence,
            }
            for e in chain.entries
        ],
    }


def test_verifier_rejects_release_authorization_hash_mismatch():
    result = SHUUDIndependentVerifier().verify_bundle(
        _bundle(forged_hash="FORGED-AUTH-HASH")
    )
    assert result.verified is False
    assert "RELEASE_AUTHORIZATION_HASH_INVALID" in result.reasons


def test_verifier_rejects_non_nef_escrow_currency():
    result = SHUUDIndependentVerifier().verify_bundle(_bundle(currency="USD"))
    assert result.verified is False
    assert "ESCROW_CURRENCY_INVALID" in result.reasons


def test_verifier_rejects_release_authorization_before_shiid_decision():
    result = SHUUDIndependentVerifier().verify_bundle(
        _bundle(order="auth_before_decision")
    )
    assert result.verified is False
    assert "SHUUD_LIFECYCLE_ORDER_INVALID" in result.reasons


def test_verifier_requires_manifest_incident_id():
    result = SHUUDIndependentVerifier().verify_bundle(
        _bundle(include_manifest_incident_id=False)
    )
    assert result.verified is False
    assert "MANIFEST_INCIDENT_ID_MISSING" in result.reasons
