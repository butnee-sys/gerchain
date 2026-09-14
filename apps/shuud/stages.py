"""SHUUD stage timing model.

This module measures elapsed time between application milestones. It does not
make policy decisions or move money.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

STAGES = (
    "incident_time",
    "evidence_locked_at",
    "verification_complete_at",
    "shiid_decided_at",
    "release_authorized_at",
    "escrow_released_at",
)


@dataclass(frozen=True)
class StageTiming:
    incident_id: str
    timestamps: Mapping[str, datetime]
    stage_seconds: Mapping[str, float]
    clearance_seconds: float
    within_two_minutes: bool


def measure_stages(
    incident_id: str,
    timestamps: Mapping[str, datetime],
) -> StageTiming:
    if not incident_id.strip():
        raise ValueError("incident_id is required")

    missing = [stage for stage in STAGES if stage not in timestamps]
    if missing:
        raise ValueError(f"missing stage timestamps: {', '.join(missing)}")

    ordered = [timestamps[stage] for stage in STAGES]
    if any(value.tzinfo is None for value in ordered):
        raise ValueError("all timestamps must be timezone-aware")

    for previous, current in zip(ordered, ordered[1:]):
        if current < previous:
            raise ValueError("stage timestamps must be monotonic")

    stage_seconds = {
        current_stage: (timestamps[current_stage] - timestamps[previous_stage]).total_seconds()
        for previous_stage, current_stage, in zip(STAGES, STAGES[1:])
    }
    clearance_seconds = (ordered[-1] - ordered[0]).total_seconds()

    return StageTiming(
        incident_id=incident_id.strip(),
        timestamps=dict(timestamps),
        stage_seconds=stage_seconds,
        clearance_seconds=clearance_seconds,
        within_two_minutes=clearance_seconds <= 120,
    )


__all__ = ["STAGES", "StageTiming", "measure_stages"]
