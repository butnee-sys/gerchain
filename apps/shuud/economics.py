"""Transparent economic measurement for SHUUD operational time savings.

The calculator intentionally accepts all monetary assumptions as inputs. GerChain
should measure observed time; it must not invent a market value for a minute.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EconomicImpact:
    incident_id: str
    baseline_seconds: float
    actual_seconds: float
    time_saved_seconds: float
    affected_vehicles: int
    vehicle_value_per_minute_mnt: float
    insurer_cost_per_minute_mnt: float
    public_road_cost_per_minute_mnt: float
    vehicle_user_savings_mnt: float
    insurer_savings_mnt: float
    public_road_savings_mnt: float
    total_savings_mnt: float


def measure_economic_impact(
    *,
    incident_id: str,
    baseline_seconds: float,
    actual_seconds: float,
    affected_vehicles: int,
    vehicle_value_per_minute_mnt: float,
    insurer_cost_per_minute_mnt: float = 0.0,
    public_road_cost_per_minute_mnt: float = 0.0,
) -> EconomicImpact:
    incident_id = incident_id.strip()
    if not incident_id:
        raise ValueError("incident_id is required")
    if baseline_seconds < 0 or actual_seconds < 0:
        raise ValueError("seconds cannot be negative")
    if affected_vehicles < 1:
        raise ValueError("affected_vehicles must be at least 1")
    if vehicle_value_per_minute_mnt < 0:
        raise ValueError("vehicle_value_per_minute_mnt cannot be negative")
    if insurer_cost_per_minute_mnt < 0 or public_road_cost_per_minute_mnt < 0:
        raise ValueError("cost per minute cannot be negative")

    saved_seconds = max(baseline_seconds - actual_seconds, 0.0)
    saved_minutes = saved_seconds / 60.0

    vehicle_user_savings = (
        saved_minutes * affected_vehicles * vehicle_value_per_minute_mnt
    )
    insurer_savings = saved_minutes * insurer_cost_per_minute_mnt
    public_road_savings = saved_minutes * public_road_cost_per_minute_mnt

    return EconomicImpact(
        incident_id=incident_id,
        baseline_seconds=baseline_seconds,
        actual_seconds=actual_seconds,
        time_saved_seconds=saved_seconds,
        affected_vehicles=affected_vehicles,
        vehicle_value_per_minute_mnt=vehicle_value_per_minute_mnt,
        insurer_cost_per_minute_mnt=insurer_cost_per_minute_mnt,
        public_road_cost_per_minute_mnt=public_road_cost_per_minute_mnt,
        vehicle_user_savings_mnt=vehicle_user_savings,
        insurer_savings_mnt=insurer_savings,
        public_road_savings_mnt=public_road_savings,
        total_savings_mnt=vehicle_user_savings + insurer_savings + public_road_savings,
    )


__all__ = ["EconomicImpact", "measure_economic_impact"]
