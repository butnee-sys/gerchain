"""Adversarial concurrency test for SHUUD authorization and release API."""

from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.testclient import TestClient

from shuud.api import (
    _AUTHORIZATIONS,
    _DECISIONS,
    _EVIDENCE,
    _ESCROWS,
    _INCIDENTS,
    _WITNESSES,
    router,
)

app = FastAPI()
app.include_router(router)


def _clear_shuud_state():
    _INCIDENTS.clear()
    _EVIDENCE.clear()
    _DECISIONS.clear()
    _AUTHORIZATIONS.clear()
    _WITNESSES.clear()
    _ESCROWS.clear()


def _approved_locked_incident(client: TestClient) -> tuple[str, str]:
    incident = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar", "vehicle_a": "A", "vehicle_b": "B"},
    )
    assert incident.status_code == 200
    incident_id = incident.json()["incident_id"]

    evidence = client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["IMG-001"],
            "gps_coordinates": "47.9184,106.9177",
            "captured_at": "2026-09-12T01:00:00+00:00",
            "vehicle_identity_refs": ["VIN-A", "VIN-B"],
            "consent_refs": ["CONSENT-A", "CONSENT-B"],
            "media_complete": True,
        },
    )
    assert evidence.status_code == 200

    decision = client.post(
        "/api/v1/shuud/decisions",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["IMG-001"],
            "damage_estimate_nef": 1_500_000,
            "two_party_consent": "PASS",
            "vehicle_identity_verified": "PASS",
            "timestamp_location_verified": "PASS",
            "media_complete": "PASS",
            "no_injury": "PASS",
            "no_third_party_property_damage": "PASS",
            "dispute_present": "FAIL",
            "fraud_flag": "FAIL",
            "insurance_valid": "PASS",
            "beneficiary_valid": "PASS",
            "witness_verified": "PASS",
        },
    )
    assert decision.status_code == 200

    escrow = client.post(
        "/api/v1/shuud/escrows",
        json={
            "incident_id": incident_id,
            "escrow_id": "ESC-RELEASE-CONCURRENT-001",
            "amount_nef": 1_500_000,
        },
    )
    assert escrow.status_code == 200
    assert escrow.json()["state"] == "LOCKED"
    return incident_id, "ESC-RELEASE-CONCURRENT-001"


def _event_types(incident_id: str) -> list[str]:
    return [entry.record.event_type for entry in _WITNESSES[incident_id].entries]


def test_concurrent_release_api_creates_one_authorization_and_one_release():
    _clear_shuud_state()
    with TestClient(app) as client:
        incident_id, escrow_id = _approved_locked_incident(client)

        def release():
            return client.post(
                "/api/v1/shuud/release",
                json={"incident_id": incident_id, "escrow_id": escrow_id},
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda _: release(), range(8)))

        statuses = [response.status_code for response in responses]
        assert statuses.count(200) == 1
        assert statuses.count(409) == 7
        assert list(_AUTHORIZATIONS) == [incident_id]
        assert _ESCROWS[escrow_id].get_state()["state"] == "RELEASED"
        assert _event_types(incident_id).count("SHUUD_RELEASE_AUTHORIZED") == 1
        assert _event_types(incident_id).count("ESCROW_RELEASED") == 1
