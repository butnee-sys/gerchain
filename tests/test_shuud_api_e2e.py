"""SHUUD HTTP E2E sandbox test.

Exercises the actual FastAPI route sequence through release. The test uses
explicit PASS gates because approval must never be the API default.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from shuud.api import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_http_incident_to_escrow_release():
    incident = client.post(
        "/api/v1/shuud/incidents",
        json={
            "location": "Ulaanbaatar",
            "vehicle_a": "1234ABC",
            "vehicle_b": "5678DEF",
        },
    )
    assert incident.status_code == 200
    incident_id = incident.json()["incident_id"]

    evidence = client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["PHOTO-001", "VIDEO-001"],
            "gps_coordinates": "47.9184,106.9177",
            "captured_at": "2026-09-12T00:00:15+00:00",
            "vehicle_identity_refs": ["VIN-A", "VIN-B"],
            "consent_refs": ["CONSENT-A", "CONSENT-B"],
            "media_complete": True,
        },
    )
    assert evidence.status_code == 200
    assert evidence.json()["state"] == "EVIDENCE_LOCKED"

    decision = client.post(
        "/api/v1/shuud/decisions",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["PHOTO-001", "VIDEO-001"],
            "damage_estimate_mnt": 1_500_000,
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
        },
    )
    assert decision.status_code == 200
    assert decision.json()["decision"] == "APPROVE"
    assert decision.json()["release_authorized"] is True

    escrow = client.post(
        "/api/v1/shuud/escrows",
        json={
            "incident_id": incident_id,
            "escrow_id": f"ESC-{incident_id}",
            "amount_mnt": 1_500_000,
        },
    )
    assert escrow.status_code == 200
    assert escrow.json()["state"] == "LOCKED"

    release = client.post(
        "/api/v1/shuud/release",
        json={
            "incident_id": incident_id,
            "escrow_id": f"ESC-{incident_id}",
        },
    )
    assert release.status_code == 200
    assert release.json()["previous_state"] == "LOCKED"
    assert release.json()["new_state"] == "RELEASED"

    metric = client.post(
        "/api/v1/shuud/metrics/clearance",
        json={
            "incident_id": incident_id,
            "incident_time": "2026-09-12T00:00:00+00:00",
            "clearance_time": "2026-09-12T00:01:00+00:00",
        },
    )
    assert metric.status_code == 200
    assert metric.json()["elapsed_seconds"] == 60.0
    assert metric.json()["within_two_minutes"] is True
