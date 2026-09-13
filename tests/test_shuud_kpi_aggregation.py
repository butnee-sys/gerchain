from shuud.kpi_api import aggregate_snapshots


def _snapshot(*, seconds: float = 100.0, economic: dict | None = None) -> dict:
    return {
        "operational_timing": {
            "incident_created_at": "2026-09-13T00:00:00+00:00",
            "clearance_confirmed_at": (
                "2026-09-13T00:01:40+00:00"
                if seconds == 100.0
                else "2026-09-13T00:03:20+00:00"
            ),
        },
        "economic_measurement": economic,
    }


def test_only_persisted_shuud_economic_v1_counts_as_economic_evidence():
    valid = {
        "model_version": "shuud-economic-v1",
        "time_saved_seconds": 60,
        "vehicle_user_savings_mnt": 100,
        "insurer_savings_mnt": 200,
        "public_road_savings_mnt": 300,
        "total_savings_mnt": 600,
    }
    invalid = {
        "model_version": "other-model",
        "time_saved_seconds": 999,
        "total_savings_mnt": 999999,
    }

    result = aggregate_snapshots([_snapshot(economic=valid), _snapshot(economic=invalid)])

    assert result["economic_measurement_cases"] == 1
    assert result["economic_coverage_rate"] == 0.5
    assert result["total_savings_mnt"] == 600


def test_clearance_target_is_applied_by_aggregation():
    result = aggregate_snapshots(
        [_snapshot(seconds=100.0), _snapshot(seconds=200.0)],
        target_seconds=150.0,
    )

    assert result["target_seconds"] == 150.0
    assert result["measured_clearance_cases"] == 2
    assert result["within_two_minutes_cases"] == 1
    assert result["within_two_minutes_rate"] == 0.5
