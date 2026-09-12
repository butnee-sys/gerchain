"""SHUUD operational timing metrics.

Operational timing is captured as a canonical lifecycle timeline so the
sandbox can measure where the two-minute clearance target is won or lost.
All timestamps are timezone-aware ISO-8601 values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping


MILESTONES = (
    "incident_created_at",
    "evidence_locked_at",
    "verification_completed_at",
    "shiid_decided_at",
    "clearance_confirmed_at",
    "settlement_released_at",
)


@dataclass(frozen=True)
class ClearanceMetric:
    incident_id: str
    incident_time: datetime
    clearance_time: datetime
    elapsed_seconds: float
    within_two_minutes: bool


@dataclass(frozen=True)
class OperationalTiming:
    """Immutable lifecycle timestamps for one SHUUD incident."""

    timestamps: Mapping[str, datetime]

    def __post_init__(self) -> None:
        unknown = set(self.timestamps) - set(MILESTONES)
        if unknown:
            raise ValueError(f"unknown operational milestones: {sorted(unknown)}")
        for name, timestamp in self.timestamps.items():
            if timestamp.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")

        ordered = [self.timestamps[name] for name in MILESTONES if name in self.timestamps]
        if ordered != sorted(ordered):
            raise ValueError("operational milestones cannot move backward in time")

    def with_milestone(self, name: str, timestamp: datetime) -> "OperationalTiming":
        if name not in MILESTONES:
            raise ValueError(f"unknown operational milestone: {name}")
        values = dict(self.timestamps)
        values[name] = timestamp
        return OperationalTiming(values)

    def as_dict(self) -> dict[str, str]:
        return {name: value.isoformat() for name, value in self.timestamps.items()}

    @classmethod
    def from_dict(cls, values: Mapping[str, str]) -> "OperationalTiming":
        return cls({name: datetime.fromisoformat(value) for name, value in values.items()})

    def duration_seconds(self, start: str, end: str) -> float | None:
        start_time = self.timestamps.get(start)
        end_time = self.timestamps.get(end)
        if start_time is None or end_time is None:
            return None
        return (end_time - start_time).total_seconds()

    def durations(self) -> dict[str, float | None]:
        pairs = {
            "incident_to_evidence_seconds": (
                "incident_created_at",
                "evidence_locked_at",
            ),
            "evidence_to_verification_seconds": (
                "evidence_locked_at",
                "verification_completed_at",
            ),
            "verification_to_shiid_seconds": (
                "verification_completed_at",
                "shiid_decided_at",
            ),
            "shiid_to_clearance_seconds": (
                "shiid_decided_at",
                "clearance_confirmed_at",
            ),
            "clearance_to_settlement_seconds": (
                "clearance_confirmed_at",
                "settlement_released_at",
            ),
            "incident_to_clearance_seconds": (
                "incident_created_at",
                "clearance_confirmed_at",
            ),
            "incident_to_settlement_seconds": (
                "incident_created_at",
                "settlement_released_at",
            ),
        }
        return {
            name: self.duration_seconds(start, end)
            for name, (start, end) in pairs.items()
        }

    def within_two_minutes(self) -> bool | None:
        elapsed = self.duration_seconds(
            "incident_created_at",
            "clearance_confirmed_at",
        )
        return None if elapsed is None else elapsed <= 120


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


__all__ = [
    "ClearanceMetric",
    "MILESTONES",
    "OperationalTiming",
    "measure_clearance",
]
