"""SHUUD measurement API input schema."""

from pydantic import BaseModel, Field


class MeasurementSummaryRequest(BaseModel):
    baseline_seconds: float = Field(ge=0)
    affected_vehicles: int | None = Field(default=None, ge=1)
    vehicle_value_per_minute_mnt: float | None = Field(default=None, ge=0)
    insurer_cost_per_minute_mnt: float = Field(default=0.0, ge=0)
    public_road_cost_per_minute_mnt: float = Field(default=0.0, ge=0)


__all__ = ["MeasurementSummaryRequest"]
