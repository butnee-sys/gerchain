"""SHUUD 90-day sandbox Day-0 configuration and status policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .command_layer import GateThresholds


class SandboxStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class SandboxConfig:
    sandbox_id: str
    name: str
    start_date: date
    end_date: date
    status: SandboxStatus
    target_seconds: float = 120.0
    go_clearance_rate: float = 0.95
    conditional_clearance_rate: float = 0.80
    go_economic_coverage: float = 0.90
    conditional_economic_coverage: float = 0.75
    minimum_cases: int = 30
    participants: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.sandbox_id.strip():
            raise ValueError("sandbox_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.target_seconds <= 0:
            raise ValueError("target_seconds must be positive")
        for value, label in (
            (self.go_clearance_rate, "go_clearance_rate"),
            (self.conditional_clearance_rate, "conditional_clearance_rate"),
            (self.go_economic_coverage, "go_economic_coverage"),
            (self.conditional_economic_coverage, "conditional_economic_coverage"),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{label} must be between 0 and 1")
        if self.conditional_clearance_rate > self.go_clearance_rate:
            raise ValueError("conditional_clearance_rate cannot exceed GO rate")
        if self.conditional_economic_coverage > self.go_economic_coverage:
            raise ValueError("conditional_economic_coverage cannot exceed GO rate")
        if self.minimum_cases < 1:
            raise ValueError("minimum_cases must be positive")

    @property
    def thresholds(self) -> GateThresholds:
        return GateThresholds(
            target_seconds=self.target_seconds,
            go_clearance_rate=self.go_clearance_rate,
            conditional_clearance_rate=self.conditional_clearance_rate,
            go_economic_coverage=self.go_economic_coverage,
            conditional_economic_coverage=self.conditional_economic_coverage,
            minimum_cases=self.minimum_cases,
        )

    def to_dict(self) -> dict:
        return {
            "sandbox_id": self.sandbox_id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status.value,
            "target_seconds": self.target_seconds,
            "go_clearance_rate": self.go_clearance_rate,
            "conditional_clearance_rate": self.conditional_clearance_rate,
            "go_economic_coverage": self.go_economic_coverage,
            "conditional_economic_coverage": self.conditional_economic_coverage,
            "minimum_cases": self.minimum_cases,
            "participants": list(self.participants),
        }

    @classmethod
    def from_dict(cls, value: dict) -> "SandboxConfig":
        return cls(
            sandbox_id=str(value["sandbox_id"]),
            name=str(value["name"]),
            start_date=date.fromisoformat(value["start_date"]),
            end_date=date.fromisoformat(value["end_date"]),
            status=SandboxStatus(value["status"]),
            target_seconds=float(value.get("target_seconds", 120.0)),
            go_clearance_rate=float(value.get("go_clearance_rate", 0.95)),
            conditional_clearance_rate=float(value.get("conditional_clearance_rate", 0.80)),
            go_economic_coverage=float(value.get("go_economic_coverage", 0.90)),
            conditional_economic_coverage=float(value.get("conditional_economic_coverage", 0.75)),
            minimum_cases=int(value.get("minimum_cases", 30)),
            participants=tuple(str(item) for item in value.get("participants", [])),
        )

    def operational_status(self, today: date) -> str:
        if self.status in (SandboxStatus.SUSPENDED, SandboxStatus.COMPLETED):
            return self.status.value
        if today < self.start_date:
            return SandboxStatus.PLANNED.value
        if today > self.end_date:
            return SandboxStatus.COMPLETED.value
        return SandboxStatus.ACTIVE.value


__all__ = ["SandboxConfig", "SandboxStatus"]
