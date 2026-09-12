"""SH-15.13 adversarial matrix for the complete SHUUD lifecycle.

The tests intentionally exercise the application boundary without introducing
another witness or money engine.  Every valid fixture is built through the
existing GerChain WitnessChain and EscrowEngine, then a single lifecycle
invariant is changed at construction time so the authoritative verifier can
reject it independently.
"""

from copy import deepcopy

import pytest

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


def _bundle(
    *,
    decision_amount=1_500_000,
    escrow_amount=1_500_000,
    currency="NEF",
    authorization_escrow_id="ESC-LIFECYCLE",
    escrow_id="ESC-LIFECYCLE",
    order="normal",
):
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
        damage_estimate_nef=decision_amount,
    )
    auth = authorize_release(decision, escrow_id=authorization_escrow_id)

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
    elif order == "decision_before_evidence":
        add_decision()
        add_evidence()
        add_auth()
    else:
        add_evidence()
        add_decision()
        add_auth()

    escrow = EscrowEngine(
        escrow_id=escrow_id,
        amount=escrow_amount,
        currency=currency,
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


def test_valid_complete_lifecycle_verifies():
    result = SHUUDIndependentVerifier().verify_bundle(_bundle())
    assert result.verified is True
    assert result.reasons == ()
    assert result.escrow_id == "ESC-LIFECYCLE"


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"authorization_escrow_id": "ESC-OTHER"}, "ESCROW_ID_MISMATCH"),
        ({"decision_amount": 1_500_000, "escrow_amount": 1_800_000}, "ESCROW_AMOUNT_MISMATCH"),
        ({"currency": "USD"}, "ESCROW_CURRENCY_INVALID"),
        ({"order": "auth_before_decision"}, "SHUUD_LIFECYCLE_ORDER_INVALID"),
        ({"order": "decision_before_evidence"}, "SHUUD_LIFECYCLE_ORDER_INVALID"),
    ],
)
def test_lifecycle_invariant_matrix_fails_closed(kwargs, reason):
    result = SHUUDIndependentVerifier().verify_bundle(_bundle(**kwargs))
    assert result.verified is False
    assert reason in result.reasons


def test_manifest_incident_identity_cannot_be_omitted():
    bundle = _bundle()
    bundle["manifest"].pop("incident_id")
    # The authoritative GerChain verifier must reject the manifest/hash pair
    # before SHUUD is allowed to interpret the lifecycle.
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_release_authorization_hash_is_bound_to_decision_and_amount():
    bundle = _bundle()
    auth_entry = next(
        entry
        for entry in bundle["entries"]
        if entry["event_payload"].get("event_type") == "SHUUD_RELEASE_AUTHORIZED"
    )
    forged = deepcopy(auth_entry["event_payload"]["payload"])
    forged["damage_estimate_nef"] = 1_800_000
    auth_entry["event_payload"]["payload"] = forged

    # The mutation is cryptographically bound to the authoritative witness
    # record, so the base verifier must fail closed rather than accepting a
    # semantically forged authorization.
    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_repeated_release_event_is_rejected_by_authoritative_witness_verifier():
    bundle = _bundle()
    replayed = deepcopy(bundle["entries"][-1])
    bundle["entries"].append(replayed)

    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_escrow_sequence_mutation_is_rejected_by_authoritative_verifier():
    bundle = _bundle()
    transition_entries = [
        entry
        for entry in bundle["entries"]
        if entry["record"].get("event_type") == "ESCROW_TRANSITION"
    ]
    transition_entries[1]["event_payload"]["sequence"] = 3

    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_incident_event_payload_tampering_cannot_cross_verification_boundary():
    bundle = _bundle()
    shuud_entry = next(
        entry
        for entry in bundle["entries"]
        if entry["event_payload"].get("event_type") == "SHUUD_EVIDENCE_LOCKED"
    )
    shuud_entry["event_payload"]["incident_id"] = "INC-FORGED"

    result = SHUUDIndependentVerifier().verify_bundle(bundle)
    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons
