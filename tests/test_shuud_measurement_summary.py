from datetime import datetime, timedelta, timezone

import pytest

from shuud.measurement_summary import build_measurement_summary
from shuud.metrics import OperationalTiming


def _timing(clearance_seconds: int = 110, settlement_seconds: int = 118) -> OperationalTiming:
    start = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
    timing = OperationalTiming({}).with_milestone("incident_created_at", start)
    timing = timing.with_milestone(
        "clearance_confirmed_at", start + timedelta(seconds=clearance_seconds)
    )
    timing = timing.with_milestone(
        "settlement_released_at", start + timedelta(seconds=settlement_seconds)
    )
    return timing


def test_measurement_summary_combines_timing_and_economics() -> None:
    summary = build_measurement_summary(
        incident_id="INC-1",
        timing=_timing(),
        baseline_seconds=300,
        affected_vehicles=3,
        vehicle_value_per_minute_mnt=1000,
        insurer_cost_per_minute_mnt=500,
        public_road_cost_per_minute_mnt=250,
    )

    assert summary.actual_clearance_seconds == 110.0
    assert summary.actual_settlement_seconds == 118.0
    assert summary.within_two_minutes is True
    assert summary.economic_impact is not None
    assert summary.economic_impact.time_saved_seconds == 190.0
    assert summary.economic_impact.total_savings_mnt == pytest.approx(12_666.6666667)


def test_measurement_summary_can_measure_timing_without_money_assumptions() -> None:
    summary = build_measurement_summary(
        incident_id="INC-2",
        timing=_timing(121, 130),
        baseline_seconds=300,
    )

    assert summary.within_two_minutes is False
    assert summary.economic_impact is None


def test_measurement_summary_requires_complete_economic_inputs() -> None:
    with pytest.raises(ValueError, match="must be supplied together"):
        build_measurement_summary(
            incident_id="INC-3",
            timing=_timing(),
            baseline_seconds=300,
            affected_vehicles=2,
        )


def test_measurement_summary_requires_clearance_for_economic_measurement() -> None:
    timing = OperationalTiming({}).with_milestone(
        "incident_created_at", datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
    )
    with pytest.raises(ValueError, match="clearance timing is required"):
        build_measurement_summary(
            incident_id="INC-4",
            timing=timing,
            baseline_seconds=300,
            affected_vehicles=2,
            vehicle_value_per_minute_mnt=1000,
        )
