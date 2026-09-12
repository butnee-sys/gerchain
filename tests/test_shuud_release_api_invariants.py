"""API-level adversarial tests for SHUUD release state invariants."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from shuud.api import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


GATES = {
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


def _prepare_locked_escrow():
    incident_id = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar"},
    ).json()["incident_id"]

    evidence = client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["release-photo"],
            "gps_coordinates": "47.918,106.917",
            "captured_at": "2026-09-12T00:00:10+00:00",
            "vehicle_identity_refs": ["vehicle-a", "vehicle-b"],
            "consent_refs": ["consent-a", "consent-b"],
            "media_complete": True,
        },
    )
    assert evidence.status_code == 200

    decision = client.post(
        "/api/v1/shuud/decisions",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["release-photo"],
            "damage_estimate_nef": 1_500_000,
            **GATES,
        },
    )
    assert decision.status_code == 200

    escrow = client.post(
        "/api/v1/shuud/escrows",
        json={
            "incident_id": incident_id,
            "escrow_id": f"ESC-RELEASE-{incident_id}",
            "amount_nef": 1_500_000,
        },
    )
    assert escrow.status_code == 200
    assert escrow.json()["state"] == "LOCKED"

    return incident_id, escrow.json()["escrow_id"]


def test_api_rejects_repeated_release_after_escrow_is_released():
    incident_id, escrow_id = _prepare_locked_escrow()

    first = client.post(
        "/api/v1/shuud/release",
        json={"incident_id": incident_id, "escrow_id": escrow_id},
    )
    assert first.status_code == 200
    assert first.json()["previous_state"] == "LOCKED"
    assert first.json()["new_state"] == "RELEASED"

    second = client.post(
        "/api/v1/shuud/release",
        json={"incident_id": incident_id, "escrow_id": escrow_id},
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "ESCROW_NOT_LOCKED"
