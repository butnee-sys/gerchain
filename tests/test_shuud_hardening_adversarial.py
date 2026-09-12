"""Adversarial tests for SHUUD fail-closed lifecycle invariants."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from escrow.engine import EscrowEngine
from shuud.api import router
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


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _bundle_with_duplicate(event_type: str):
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
    record_evidence_locked(chain, evidence, timestamp="2026-09-12T00:00:15+00:00")

    decision = SHIIDDecision(
        incident_id=incident.incident_id,
        decision=Decision.APPROVE,
        rule_version="SHUUD-POLICY-1",
        reasons=(),
        damage_estimate_nef=1_500_000,
    )
    record_shiid_decision(chain, decision, timestamp="2026-09-12T00:00:20+00:00")

    auth = authorize_release(decision, escrow_id="ESC-DUP")
    record_release_authorized(chain, auth, timestamp="2026-09-12T00:00:25+00:00")

    if event_type == "SHUUD_EVIDENCE_LOCKED":
        record_evidence_locked(chain, evidence, timestamp="2026-09-12T00:00:26+00:00")
    elif event_type == "SHIID_DECISION":
        record_shiid_decision(chain, decision, timestamp="2026-09-12T00:00:27+00:00")
    elif event_type == "SHUUD_RELEASE_AUTHORIZED":
        record_release_authorized(chain, auth, timestamp="2026-09-12T00:00:28+00:00")
    else:
        raise AssertionError(event_type)

    escrow = EscrowEngine(
        escrow_id="ESC-DUP",
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
    return bundle


def test_verifier_rejects_duplicate_evidence_locked_event():
    result = SHUUDIndependentVerifier().verify_bundle(
        _bundle_with_duplicate("SHUUD_EVIDENCE_LOCKED")
    )
    assert result.verified is False
    assert "SHUUD_LIFECYCLE_DUPLICATE_OR_MISSING" in result.reasons


def test_verifier_rejects_duplicate_shiid_decision_event():
    result = SHUUDIndependentVerifier().verify_bundle(
        _bundle_with_duplicate("SHIID_DECISION")
    )
    assert result.verified is False
    assert "SHUUD_LIFECYCLE_DUPLICATE_OR_MISSING" in result.reasons


def test_verifier_rejects_duplicate_release_authorization_event():
    result = SHUUDIndependentVerifier().verify_bundle(
        _bundle_with_duplicate("SHUUD_RELEASE_AUTHORIZED")
    )
    assert result.verified is False
    assert "SHUUD_LIFECYCLE_DUPLICATE_OR_MISSING" in result.reasons


def _approve_api_incident():
    incident_id = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar"},
    ).json()["incident_id"]
    evidence = client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["photo-duplicate"],
            "gps_coordinates": "47.918,106.917",
            "captured_at": "2026-09-12T00:00:10+00:00",
            "vehicle_identity_refs": ["vehicle-a", "vehicle-b"],
            "consent_refs": ["consent-a", "consent-b"],
            "media_complete": True,
        },
    )
    assert evidence.status_code == 200
    gates = {key: "PASS" for key in (
        "two_party_consent",
        "vehicle_identity_verified",
        "timestamp_location_verified",
        "media_complete",
        "no_injury",
        "no_third_party_property_damage",
        "dispute_present",
        "fraud_flag",
        "insurance_valid",
        "beneficiary_valid",
        "witness_verified",
    )}
    decision = client.post(
        "/api/v1/shuud/decisions",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["photo-duplicate"],
            "damage_estimate_nef": 1_500_000,
            **gates,
        },
    )
    assert decision.status_code == 200
    return incident_id


def test_api_rejects_duplicate_evidence_lock():
    incident_id = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar"},
    ).json()["incident_id"]
    payload = {
        "incident_id": incident_id,
        "evidence_refs": ["photo-1"],
        "gps_coordinates": "47.918,106.917",
        "captured_at": "2026-09-12T00:00:10+00:00",
        "vehicle_identity_refs": ["vehicle-a", "vehicle-b"],
        "consent_refs": ["consent-a", "consent-b"],
        "media_complete": True,
    }
    assert client.post("/api/v1/shuud/evidence", json=payload).status_code == 200
    response = client.post("/api/v1/shuud/evidence", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "EVIDENCE_ALREADY_LOCKED"


def test_api_rejects_duplicate_decision():
    incident_id = _approve_api_incident()
    response = client.post(
        "/api/v1/shuud/decisions",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["photo-duplicate"],
            "damage_estimate_nef": 1_500_000,
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "DECISION_ALREADY_EXISTS"
