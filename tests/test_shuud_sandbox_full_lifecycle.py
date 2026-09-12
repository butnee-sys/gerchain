"""Standalone SHUUD sandbox full-lifecycle integration test.

Exercises the same authoritative lifecycle used by the production-readiness
and measurement E2E suites, while keeping all sandbox economic assumptions
explicit.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from shuud.api import router


def _pass_gate_payload() -> dict:
    return {
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


def test_shuud_full_sandbox_lifecycle() -> None:
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    incident = client.post(
        "/api/v1/shuud/incidents",
        json={
            "location": "SANDBOX",
            "vehicle_a": "TEST-A",
            "vehicle_b": "TEST-B",
            "description": "Day-0 full lifecycle",
        },
    )
    assert incident.status_code == 200
    incident_id = incident.json()["incident_id"]

    evidence_refs = [f"sandbox:evidence:{incident_id}"]
    evidence = client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": evidence_refs,
            "gps_coordinates": "SANDBOX",
            "captured_at": "2026-09-12T19:30:00+00:00",
            "vehicle_identity_refs": ["TEST-A", "TEST-B"],
            "consent_refs": ["CONSENT-A", "CONSENT-B"],
            "media_complete": True,
        },
    )
    assert evidence.status_code == 200
    assert evidence.json()["state"] == "EVIDENCE_LOCKED"

    decision_payload = {
        "incident_id": incident_id,
        "evidence_refs": evidence_refs,
        "damage_estimate_mnt": 1_000_000,
        **_pass_gate_payload(),
    }
    decision = client.post("/api/v1/shuud/decisions", json=decision_payload)
    assert decision.status_code == 200
    assert decision.json()["decision"] == "APPROVE"

    escrow_id = f"SANDBOX-{incident_id}"
    escrow = client.post(
        "/api/v1/shuud/escrows",
        json={
            "incident_id": incident_id,
            "escrow_id": escrow_id,
            "amount_mnt": 1_000_000,
            "settlement_provider": "NEF",
        },
    )
    assert escrow.status_code == 200
    assert escrow.json()["currency"] == "MNT"
    assert escrow.json()["settlement_provider"] == "NEF"
    assert escrow.json()["state"] == "LOCKED"

    clearance = client.post(
        "/api/v1/shuud/metrics/clearance",
        json={"incident_id": incident_id},
    )
    assert clearance.status_code == 200
    assert clearance.json()["incident_id"] == incident_id
    assert clearance.json()["elapsed_seconds"] >= 0

    release = client.post(
        "/api/v1/shuud/release",
        json={"incident_id": incident_id, "escrow_id": escrow_id},
    )
    assert release.status_code == 200
    assert release.json()["new_state"] == "RELEASED"

    summary = client.post(
        f"/api/v1/shuud/metrics/{incident_id}/summary",
        json={
            "baseline_seconds": 600,
            "affected_vehicles": 2,
            "vehicle_value_per_minute_mnt": 1000,
            "insurer_cost_per_minute_mnt": 500,
            "public_road_cost_per_minute_mnt": 750,
        },
    )
    assert summary.status_code == 200
    body = summary.json()
    assert body["incident_id"] == incident_id
    assert body["economic_impact"] is not None
    assert body["economic_impact"]["total_savings_mnt"] >= 0

    metrics = client.get(f"/api/v1/shuud/metrics/{incident_id}")
    assert metrics.status_code == 200
    metric_body = metrics.json()
    assert metric_body["snapshot_persisted"] is True
    assert metric_body["milestones"]["incident_created_at"] is not None
    assert metric_body["milestones"]["clearance_confirmed_at"] is not None
    assert metric_body["milestones"]["settlement_released_at"] is not None
