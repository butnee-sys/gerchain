import os

from fastapi.testclient import TestClient

import shuud.api as shuud_api
from gerchain.web_ui import app
from shuud.persistence import SHUUDPersistence
from shuud.runtime_store import SHUUDRuntimeStore


def _reset_state():
    shuud_api._INCIDENTS.clear()
    shuud_api._EVIDENCE.clear()
    shuud_api._DECISIONS.clear()
    shuud_api._AUTHORIZATIONS.clear()
    shuud_api._WITNESSES.clear()
    shuud_api._ESCROWS.clear()


def test_shuud_api_recovers_after_in_memory_state_loss(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'shuud-api.db'}"
    persistence = SHUUDPersistence(db_url)
    monkeypatch.setattr(shuud_api, "_PERSISTENCE", persistence)
    monkeypatch.setattr(shuud_api, "_RUNTIME_STORE", SHUUDRuntimeStore(persistence))
    _reset_state()

    client = TestClient(app)

    incident = client.post(
        "/api/v1/shuud/incidents",
        json={
            "location": "Ulaanbaatar",
            "vehicle_a": "1234ABC",
            "vehicle_b": "5678DEF",
        },
    ).json()
    incident_id = incident["incident_id"]

    evidence = client.post(
        "/api/v1/shuud/evidence",
        json={
            "incident_id": incident_id,
            "evidence_refs": ["PHOTO-R-001", "VIDEO-R-001"],
            "gps_coordinates": "47.9184,106.9177",
            "captured_at": "2026-09-13T00:00:15+00:00",
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
            "evidence_refs": ["PHOTO-R-001", "VIDEO-R-001"],
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

    escrow = client.post(
        "/api/v1/shuud/escrows",
        json={
            "incident_id": incident_id,
            "escrow_id": f"ESC-{incident_id}",
            "amount_mnt": 1_500_000,
            "settlement_provider": "NEF",
        },
    )
    assert escrow.status_code == 200
    assert escrow.json()["currency"] == "MNT"
    assert escrow.json()["settlement_provider"] == "NEF"

    # Simulate process restart: all application-memory registries disappear.
    _reset_state()

    release = client.post(
        "/api/v1/shuud/release",
        json={
            "incident_id": incident_id,
            "escrow_id": f"ESC-{incident_id}",
        },
    )

    assert release.status_code == 200
    payload = release.json()
    assert payload["previous_state"] == "LOCKED"
    assert payload["new_state"] == "RELEASED"

    witness = shuud_api._WITNESSES[incident_id]
    escrow_engine = shuud_api._ESCROWS[f"ESC-{incident_id}"]
    assert escrow_engine.get_state()["state"] == "RELEASED"
    assert witness.entries[-1].event_payload["currency"] == "MNT"
    assert witness.entries[-1].evidence["settlement_provider"] == "NEF"

    _reset_state()
