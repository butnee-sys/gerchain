"""SHUUD operational timing metrics.

The sandbox KPI is measured from incident creation to clearance/release.
All timestamps are timezone-aware ISO-8601 values.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ClearanceMetric:
    incident_id: str
    incident_time: datetime
    clearance_time: datetime
    elapsed_seconds: float
    within_two_minutes: bool


def measure_clearance(
    incident_id: str,
    incident_time: datetime,
    clearance_time: datetime,
) -> ClearanceMetric:
    if not incident_id.strip():
        raise ValueError("incident_id is required")
    if incident_time.tzinfo is None or clearance_time.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")

    elapsed = (clearance_time - incident_time).total_seconds()
    if elapsed < 0:
        raise ValueError("clearance_time cannot precede incident_time")

    return ClearanceMetric(
        incident_id=incident_id.strip(),
        incident_time=incident_time,
        clearance_time=clearance_time,
        elapsed_seconds=elapsed,
        within_two_minutes=elapsed <= 120,
    )


__all__ = ["ClearanceMetric", "measure_clearance"]
