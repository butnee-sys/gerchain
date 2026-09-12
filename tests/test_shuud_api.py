"""HTTP-level SHUUD API lifecycle tests.

These tests validate that the API does not reconstruct unknown incidents,
does not accept orphan evidence, and fails closed when policy gates are not
explicitly satisfied.
"""

from fastapi.testclient import TestClient

from shuud.api import router
from fastapi import FastAPI


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_evidence_requires_existing_incident():
    response = client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": "INC-MISSING",
            "evidence_refs": ["photo-1"],
            "gps_coordinates": "47.918,106.917",
            "captured_at": "2026-09-12T00:00:10+00:00",
            "vehicle_identity_refs": ["vehicle-a", "vehicle-b"],
            "consent_refs": ["consent-a", "consent-b"],
            "media_complete": True,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "INCIDENT_NOT_FOUND"


def test_decision_fails_closed_by_default():
    incident = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar"},
    ).json()
    incident_id = incident["incident_id"]

    client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["photo-1"],
            "gps_coordinates": "47.918,106.917",
            "captured_at": "2026-09-12T00:00:10+00:00",
            "vehicle_identity_refs": ["vehicle-a", "vehicle-b"],
            "consent_refs": ["consent-a", "consent-b"],
            "media_complete": True,
        },
    )

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
    incident = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar"},
    ).json()
    incident_id = incident["incident_id"]

    client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["photo-1"],
            "gps_coordinates": "47.918,106.917",
            "captured_at": "2026-09-12T00:00:10+00:00",
            "vehicle_identity_refs": ["vehicle-a", "vehicle-b"],
            "consent_refs": ["consent-a", "consent-b"],
            "media_complete": True,
        },
    )

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
