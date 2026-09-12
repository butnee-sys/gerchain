from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from shuud.api import router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _allow_decision(client: TestClient, incident_id: str) -> None:
    evidence = client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["PHOTO-1"],
            "gps_coordinates": "47.9184,106.9177",
            "captured_at": "2026-09-13T00:00:15+00:00",
            "vehicle_identity_refs": ["VIN-A", "VIN-B"],
            "consent_refs": ["CONSENT-A", "CONSENT-B"],
            "media_complete": True,
        },
    )
    assert evidence.status_code == 200
    response = client.post(
        "/api/v1/shuud/decisions",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["PHOTO-1"],
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
    assert response.status_code == 200
    assert response.json()["decision"] == "APPROVE"


def test_measurement_summary_api_exposes_timing_and_economics() -> None:
    client = _client()
    incident_response = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar", "vehicle_a": "1234ABC", "vehicle_b": "5678DEF"},
    )
    assert incident_response.status_code == 200
    incident_id = incident_response.json()["incident_id"]

    _allow_decision(client, incident_id)

    created = datetime.fromisoformat(incident_response.json()["occurred_at"])
    clearance = created + timedelta(seconds=110)
    settlement = clearance + timedelta(seconds=8)

    clearance_response = client.post(
        "/api/v1/shuud/metrics/clearance",
        json={"incident_id": incident_id, "clearance_time": clearance.isoformat()},
    )
    assert clearance_response.status_code == 200

    from shuud.api import _PERSISTENCE

    snapshot = _PERSISTENCE.load_snapshot(incident_id)
    assert snapshot is not None
    timing = dict(snapshot["operational_timing"])
    timing["settlement_released_at"] = settlement.isoformat()
    _PERSISTENCE.save_snapshot(incident_id, {**snapshot, "operational_timing": timing})

    response = client.post(
        f"/api/v1/shuud/metrics/{incident_id}/summary",
        json={
            "baseline_seconds": 300,
            "affected_vehicles": 3,
            "vehicle_value_per_minute_mnt": 1000,
            "insurer_cost_per_minute_mnt": 500,
            "public_road_cost_per_minute_mnt": 250,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["actual_clearance_seconds"] == 110.0
    assert data["actual_settlement_seconds"] == 118.0
    assert data["within_two_minutes"] is True
    assert data["economic_impact"]["time_saved_seconds"] == 190.0
    assert data["economic_impact"]["total_savings_mnt"] == 12666.666666666666


def test_measurement_summary_api_supports_timing_only() -> None:
    client = _client()
    incident = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar"},
    )
    assert incident.status_code == 200
    incident_id = incident.json()["incident_id"]
    created = datetime.fromisoformat(incident.json()["occurred_at"])
    clearance = created + timedelta(seconds=121)
    response = client.post(
        "/api/v1/shuud/metrics/clearance",
        json={"incident_id": incident_id, "clearance_time": clearance.isoformat()},
    )
    assert response.status_code == 200

    response = client.post(
        f"/api/v1/shuud/metrics/{incident_id}/summary",
        json={"baseline_seconds": 300},
    )
    assert response.status_code == 200
    assert response.json()["within_two_minutes"] is False
    assert response.json()["economic_impact"] is None
