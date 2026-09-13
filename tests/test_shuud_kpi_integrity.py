from shuud.kpi_api import aggregate_snapshots


def _snapshot(
    incident_id: str,
    *,
    clearance_seconds: float | None = None,
    economic: dict | None = None,
    approved: bool = False,
    released: bool = False,
) -> dict:
    timing = {
        "incident_created_at": "2026-09-12T00:00:00+00:00",
    }
    if clearance_seconds is not None:
        from datetime import datetime, timedelta, timezone

        created = datetime.fromisoformat(timing["incident_created_at"])
        timing["clearance_confirmed_at"] = (
            created + timedelta(seconds=clearance_seconds)
        ).astimezone(timezone.utc).isoformat()

    snapshot = {
        "incident": {"incident_id": incident_id},
        "operational_timing": timing,
        "decision": {"decision": "APPROVE" if approved else "REJECT"},
        "escrow": {"state": {"state": "RELEASED" if released else "LOCKED"}},
    }
    if economic is not None:
        snapshot["economic_measurement"] = economic
    return snapshot


def test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics():
    snapshots = [
        _snapshot(
            "INC-001",
            clearance_seconds=90,
            economic={
                "time_saved_seconds": 510,
                "vehicle_user_savings_mnt": 8500,
                "insurer_savings_mnt": 4250,
                "public_road_savings_mnt": 6800,
                "total_savings_mnt": 19550,
            },
            approved=True,
            released=True,
        ),
        _snapshot("INC-002", clearance_seconds=180, approved=False),
    ]

    result = aggregate_snapshots(snapshots)

    assert result["total_cases"] == 2
    assert result["measured_clearance_cases"] == 2
    assert result["within_two_minutes_cases"] == 1
    assert result["within_two_minutes_rate"] == 0.5
    assert result["shiid_approved_cases"] == 1
    assert result["release_success_cases"] == 1
    assert result["economic_measurement_cases"] == 1
    assert result["economic_coverage_rate"] == 0.5
    assert result["total_time_saved_seconds"] == 510
    assert result["total_time_saved_minutes"] == 8.5
    assert result["total_savings_mnt"] == 19550


def test_updated_economic_measurement_replaces_previous_value_without_double_count():
    first = _snapshot(
        "INC-003",
        clearance_seconds=100,
        economic={
            "time_saved_seconds": 500,
            "vehicle_user_savings_mnt": 1000,
            "insurer_savings_mnt": 200,
            "public_road_savings_mnt": 300,
            "total_savings_mnt": 1500,
        },
    )
    updated = _snapshot(
        "INC-003",
        clearance_seconds=100,
        economic={
            "time_saved_seconds": 500,
            "vehicle_user_savings_mnt": 2000,
            "insurer_savings_mnt": 400,
            "public_road_savings_mnt": 600,
            "total_savings_mnt": 3000,
        },
    )

    # Canonical persistence has one row per incident; an update replaces the
    # snapshot rather than creating another aggregate contribution.
    result = aggregate_snapshots([updated])

    assert result["total_cases"] == 1
    assert result["economic_measurement_cases"] == 1
    assert result["total_time_saved_seconds"] == 500
    assert result["total_savings_mnt"] == 3000
    assert result["total_savings_mnt"] != 1500 + 3000
    assert first["incident"]["incident_id"] == updated["incident"]["incident_id"]


def test_kpi_rejects_negative_clearance_duration_from_measurement_set():
    snapshot = _snapshot("INC-004", clearance_seconds=120)
    snapshot["operational_timing"]["clearance_confirmed_at"] = (
        "2026-09-11T23:59:00+00:00"
    )

    result = aggregate_snapshots([snapshot])

    assert result["total_cases"] == 1
    assert result["measured_clearance_cases"] == 0
    assert result["within_two_minutes_cases"] == 0
    assert result["average_clearance_seconds"] is None
