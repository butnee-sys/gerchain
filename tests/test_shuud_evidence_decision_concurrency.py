"""Adversarial concurrency tests for SHUUD evidence and decision creation."""

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


def _create_incident(client: TestClient) -> str:
    response = client.post(
        "/api/v1/shuud/incidents",
        json={"location": "Ulaanbaatar", "vehicle_a": "A", "vehicle_b": "B"},
    )
    assert response.status_code == 200
    return response.json()["incident_id"]


def _evidence_payload(incident_id: str) -> dict:
    return {
        "incident_id": incident_id,
        "evidence_refs": ["IMG-001"],
        "gps_coordinates": "47.9184,106.9177",
        "captured_at": "2026-09-12T01:00:00+00:00",
        "vehicle_identity_refs": ["VIN-A", "VIN-B"],
        "consent_refs": ["CONSENT-A", "CONSENT-B"],
        "media_complete": True,
    }


def _decision_payload(incident_id: str) -> dict:
    return {
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
    }


def _event_types(incident_id: str) -> list[str]:
    witness = _WITNESSES[incident_id]
    return [entry.record.event_type for entry in witness.entries]


def test_concurrent_evidence_lock_allows_exactly_one_authoritative_event():
    _clear_shuud_state()
    with TestClient(app) as client:
        incident_id = _create_incident(client)

        def lock_evidence():
            return client.post("/api/v1/shuud/evidence", json=_evidence_payload(incident_id))

        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda _: lock_evidence(), range(8)))

        statuses = [response.status_code for response in responses]
        assert statuses.count(200) == 1
        assert statuses.count(409) == 7
        assert list(_EVIDENCE) == [incident_id]
        assert _event_types(incident_id).count("SHUUD_EVIDENCE_LOCKED") == 1


def test_concurrent_shiid_decision_allows_exactly_one_authoritative_event():
    _clear_shuud_state()
    with TestClient(app) as client:
        incident_id = _create_incident(client)
        evidence = client.post("/api/v1/shuud/evidence", json=_evidence_payload(incident_id))
        assert evidence.status_code == 200

        def make_decision():
            return client.post("/api/v1/shuud/decisions", json=_decision_payload(incident_id))

        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda _: make_decision(), range(8)))

        statuses = [response.status_code for response in responses]
        assert statuses.count(200) == 1
        assert statuses.count(409) == 7
        assert list(_DECISIONS) == [incident_id]
        assert _event_types(incident_id).count("SHIID_DECISION") == 1
