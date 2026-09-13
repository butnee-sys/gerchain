import json

from shuud.kpi_api import _aggregate
from shuud.persistence import SHUUDPersistence


def _snapshot(total_savings=100.0):
    return {
        "incident": {"incident_id": "INC-ECON-001"},
        "operational_timing": {
            "incident_created_at": "2026-09-13T00:00:00+00:00",
            "clearance_confirmed_at": "2026-09-13T00:01:00+00:00",
        },
        "economic_measurement": {
            "model_version": "shuud-economic-v1",
            "baseline_seconds": 600.0,
            "actual_clearance_seconds": 60.0,
            "time_saved_seconds": 540.0,
            "affected_vehicles": 2,
            "vehicle_value_per_minute_mnt": 1000.0,
            "insurer_cost_per_minute_mnt": 500.0,
            "public_road_cost_per_minute_mnt": 800.0,
            "vehicle_user_savings_mnt": 18000.0,
            "insurer_savings_mnt": 4500.0,
            "public_road_savings_mnt": 7200.0,
            "total_savings_mnt": total_savings,
        },
        "decision": {"decision": "APPROVE"},
        "escrow": {"state": {"state": "RELEASED"}},
    }


def test_economic_measurement_is_atomically_persisted(tmp_path):
    store = SHUUDPersistence(f"sqlite:///{tmp_path / 'shuud.db'}")
    original = {"operational_timing": {"incident_created_at": "2026-09-13T00:00:00+00:00"}}
    store.save_snapshot("INC-ECON-001", original)

    assert store.save_economic_measurement_if_current(
        "INC-ECON-001",
        original,
        {"model_version": "shuud-economic-v1", "total_savings_mnt": 29700.0},
    )

    reopened = SHUUDPersistence(f"sqlite:///{tmp_path / 'shuud.db'}")
    loaded = reopened.load_snapshot("INC-ECON-001")
    assert loaded["economic_measurement"]["model_version"] == "shuud-economic-v1"
    assert loaded["economic_measurement"]["total_savings_mnt"] == 29700.0


def test_economic_measurement_rejects_stale_snapshot(tmp_path):
    store = SHUUDPersistence(f"sqlite:///{tmp_path / 'shuud.db'}")
    original = {"status": "initial"}
    store.save_snapshot("INC-ECON-001", original)
    store.save_snapshot("INC-ECON-001", {"status": "changed"})

    assert not store.save_economic_measurement_if_current(
        "INC-ECON-001",
        original,
        {"model_version": "shuud-economic-v1", "total_savings_mnt": 1.0},
    )
    assert store.load_snapshot("INC-ECON-001") == {"status": "changed"}


def test_economic_fields_are_json_durable():
    snapshot = _snapshot(29700.0)
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    decoded = json.loads(encoded)
    assert decoded["economic_measurement"]["total_savings_mnt"] == 29700.0


def test_aggregate_includes_persisted_economic_values(monkeypatch):
    monkeypatch.setattr("shuud.kpi_api._rows", lambda start_at=None: [_snapshot(29700.0)])
    kpi = _aggregate()

    assert kpi["economic_measurement_cases"] == 1
    assert kpi["total_time_saved_seconds"] == 540.0
    assert kpi["total_savings_mnt"] == 29700.0
    assert kpi["total_vehicle_user_savings_mnt"] == 18000.0
    assert kpi["total_insurer_savings_mnt"] == 4500.0
    assert kpi["total_public_road_savings_mnt"] == 7200.0
