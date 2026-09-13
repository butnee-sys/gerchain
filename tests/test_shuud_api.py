"""HTTP-level SHUUD API lifecycle tests.

These tests validate the fail-closed decision boundary and the sandbox
lifecycle used by the investor/municipal demonstration UI.
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from shuud.api import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _evidence(incident_id: str, refs: list[str] | None = None):
    refs = refs or ["photo-1"]
    return client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": refs,
            "gps_coordinates": "47.918,106.917",
            "captured_at": "2026-09-12T00:00:10+00:00",
            "vehicle_identity_refs": ["vehicle-a", "vehicle-b"],
            "consent_refs": ["consent-a", "consent-b"],
            "media_complete": True,
        },
    )


def _approve(incident_id: str, refs: list[str] | None = None):
    refs = refs or ["photo-1"]
    gates = {
        "two_party_consent": "PASS",
        "vehicle_identity_verified": "PASS",
        "timestamp_location_verified": "PASS",
        "media_complete": "PASS",
        "no_injury": "PASS",
        "no_third_party_property_damage": "PASS",
        "dispute_present": "PASS",
        "fraud_flag": "PASS",
        "insurance_valid": "PASS",
        "beneficiary_valid": "PASS",
        "witness_verified": "PASS",
    }
    return client.post(
        "/api/v1/shuud/decisions",
        json={
            "incident_id": incident_id,
            "evidence_refs": refs,
            "damage_estimate_mnt": 1_500_000,
            **gates,
        },
    )


def test_evidence_requires_existing_incident():
    response = _evidence("INC-MISSING", ["photo-1"])
    assert response.status_code == 404
    assert response.json()["detail"] == "INCIDENT_NOT_FOUND"


def test_decision_fails_closed_by_default():
    incident_id = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar"},
    ).json()["incident_id"]

    assert _evidence(incident_id).status_code == 200
    response = client.post(
        "/api/v1/shuud/decisions",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["photo-1"],
            "damage_estimate_mnt": 1_500_000,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "HUMAN_REVIEW"
    assert body["release_authorized"] is False


def test_decision_rejects_evidence_reference_mismatch():
    incident_id = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar"},
    ).json()["incident_id"]

    assert _evidence(incident_id).status_code == 200
    response = client.post(
        "/api/v1/shuud/decisions",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["photo-forged"],
            "damage_estimate_mnt": 1_500_000,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "EVIDENCE_REFERENCE_MISMATCH"


def test_full_sandbox_lifecycle_reaches_payment_release():
    occurred_at = datetime.now(timezone.utc).isoformat()
    incident = client.post(
        "/api/v1/shuud/incidents",
        json={
            "location": "СБД · Энхтайвны өргөн чөлөө",
            "vehicle_a": "UB-0001",
            "vehicle_b": "UB-0002",
            "description": "SHUUD sandbox minor road incident",
            "occurred_at": occurred_at,
        },
    )
    assert incident.status_code == 200
    incident_id = incident.json()["incident_id"]

    evidence = _evidence(incident_id)
    assert evidence.status_code == 200

    decision = _approve(incident_id)
    assert decision.status_code == 200
    assert decision.json()["decision"] == "APPROVE"
    assert decision.json()["release_authorized"] is True

    escrow_id = f"ESC-{incident_id}"
    escrow = client.post(
        "/api/v1/shuud/escrows",
        json={
            "incident_id": incident_id,
            "escrow_id": escrow_id,
            "amount_mnt": 1_500_000,
            "settlement_provider": "NEF",
        },
    )
    assert escrow.status_code == 200
    assert escrow.json()["state"] == "LOCKED"

    clearance = client.post(
        "/api/v1/shuud/metrics/clearance",
        json={"incident_id": incident_id},
    )
    assert clearance.status_code == 200
    assert "elapsed_seconds" in clearance.json()

    release = client.post(
        "/api/v1/shuud/release",
        json={"incident_id": incident_id, "escrow_id": escrow_id},
    )
    assert release.status_code == 200
    assert release.json()["new_state"] == "RELEASED"

    metrics = client.get(f"/api/v1/shuud/metrics/{incident_id}")
    assert metrics.status_code == 200
    assert metrics.json()["snapshot_persisted"] is True
