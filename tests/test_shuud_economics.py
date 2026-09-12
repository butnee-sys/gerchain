from __future__ import annotations

import pytest

from shuud.economics import measure_economic_impact


def test_economic_impact_sums_transparent_components() -> None:
    impact = measure_economic_impact(
        incident_id="INC-ECON-1",
        baseline_seconds=600,
        actual_seconds=120,
        affected_vehicles=3,
        vehicle_value_per_minute_mnt=5000,
        insurer_cost_per_minute_mnt=1000,
        public_road_cost_per_minute_mnt=500,
    )

    # 480 seconds = 8 minutes.
    assert impact.time_saved_seconds == 480
    assert impact.vehicle_user_savings_mnt == 120000
    assert impact.insurer_savings_mnt == 8000
    assert impact.public_road_savings_mnt == 4000
    assert impact.total_savings_mnt == 132000


def test_economic_impact_does_not_claim_negative_savings() -> None:
    impact = measure_economic_impact(
        incident_id="INC-ECON-2",
        baseline_seconds=100,
        actual_seconds=130,
        affected_vehicles=2,
        vehicle_value_per_minute_mnt=5000,
    )
    assert impact.time_saved_seconds == 0
    assert impact.total_savings_mnt == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"incident_id": "", "baseline_seconds": 100, "actual_seconds": 50},
        {"incident_id": "INC", "baseline_seconds": -1, "actual_seconds": 50},
        {"incident_id": "INC", "baseline_seconds": 100, "actual_seconds": -1},
        {"incident_id": "INC", "baseline_seconds": 100, "actual_seconds": 50, "affected_vehicles": 0},
        {"incident_id": "INC", "baseline_seconds": 100, "actual_seconds": 50, "vehicle_value_per_minute_mnt": -1},
    ],
)
def test_economic_impact_validates_inputs(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        measure_economic_impact(**kwargs)
