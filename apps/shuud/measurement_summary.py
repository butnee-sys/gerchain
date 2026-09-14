"""Unified SHUUD operational and economic measurement.

This module composes the already-authoritative operational timing model with the
explicit economic assumptions from ``shuud.economics``. It does not create a
second lifecycle or alter WitnessChain/EscrowEngine authority.
"""

from __future__ import annotations

from dataclasses import dataclass

from .economics import EconomicImpact, measure_economic_impact
from .metrics import OperationalTiming


@dataclass(frozen=True)
class MeasurementSummary:
    incident_id: str
    baseline_seconds: float
    actual_clearance_seconds: float | None
    actual_settlement_seconds: float | None
    within_two_minutes: bool | None
    economic_impact: EconomicImpact | None

    def as_dict(self) -> dict:
        economic = None
        if self.economic_impact is not None:
            economic = self.economic_impact.__dict__.copy()
        return {
            "incident_id": self.incident_id,
            "baseline_seconds": self.baseline_seconds,
            "actual_clearance_seconds": self.actual_clearance_seconds,
            "actual_settlement_seconds": self.actual_settlement_seconds,
            "within_two_minutes": self.within_two_minutes,
            "economic_impact": economic,
        }


def build_measurement_summary(
    *,
    incident_id: str,
    timing: OperationalTiming,
    baseline_seconds: float,
    affected_vehicles: int | None = None,
    vehicle_value_per_minute_mnt: float | None = None,
    insurer_cost_per_minute_mnt: float = 0.0,
    public_road_cost_per_minute_mnt: float = 0.0,
) -> MeasurementSummary:
    if baseline_seconds < 0:
        raise ValueError("baseline_seconds cannot be negative")

    actual_clearance = timing.duration_seconds(
        "incident_created_at", "clearance_confirmed_at"
    )
    actual_settlement = timing.duration_seconds(
        "incident_created_at", "settlement_released_at"
    )

    economic = None
    if affected_vehicles is not None or vehicle_value_per_minute_mnt is not None:
        if affected_vehicles is None or vehicle_value_per_minute_mnt is None:
            raise ValueError(
                "affected_vehicles and vehicle_value_per_minute_mnt must be supplied together"
            )
        if actual_clearance is None:
            raise ValueError("clearance timing is required for economic measurement")
        economic = measure_economic_impact(
            incident_id=incident_id,
            baseline_seconds=baseline_seconds,
            actual_seconds=actual_clearance,
            affected_vehicles=affected_vehicles,
            vehicle_value_per_minute_mnt=vehicle_value_per_minute_mnt,
            insurer_cost_per_minute_mnt=insurer_cost_per_minute_mnt,
            public_road_cost_per_minute_mnt=public_road_cost_per_minute_mnt,
        )

    return MeasurementSummary(
        incident_id=incident_id.strip(),
        baseline_seconds=baseline_seconds,
        actual_clearance_seconds=actual_clearance,
        actual_settlement_seconds=actual_settlement,
        within_two_minutes=timing.within_two_minutes(),
        economic_impact=economic,
    )


__all__ = ["MeasurementSummary", "build_measurement_summary"]
