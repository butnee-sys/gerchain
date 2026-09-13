"""SHUUD 90-day sandbox command layer.

This module is deliberately independent from the canonical incident, SHIID,
escrow and economic-measurement authorities. It evaluates persisted evidence
and produces a decision surface; it does not create or modify settlement
state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping


LIFECYCLE = (
    "incident",
    "evidence",
    "shiid",
    "clearance",
    "escrow",
    "release",
    "economic",
)


class GateDecision(str, Enum):
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL GO"
    NO_GO = "NO-GO"


@dataclass(frozen=True)
class GateThresholds:
    """Configurable sandbox policy thresholds.

    These are decision-policy parameters, not economic assumptions. They can
    be changed by the sandbox owner without changing the measurement layer.
    """

    target_seconds: float = 120.0
    go_clearance_rate: float = 0.95
    conditional_clearance_rate: float = 0.80
    go_economic_coverage: float = 0.90
    conditional_economic_coverage: float = 0.75
    minimum_cases: int = 30


@dataclass(frozen=True)
class CaseRecord:
    case_id: str
    clearance_seconds: float | None
    economic_measured: bool
    lifecycle: tuple[str, ...] = field(default_factory=tuple)

    @property
    def within_target(self) -> bool:
        return (
            self.clearance_seconds is not None
            and self.clearance_seconds <= 120.0
        )

    @property
    def lifecycle_complete(self) -> bool:
        return tuple(self.lifecycle) == LIFECYCLE


def validate_case(case: CaseRecord, *, target_seconds: float = 120.0) -> dict:
    """Return case-level evidence without changing persisted state."""
    elapsed = case.clearance_seconds
    within = elapsed is not None and elapsed <= target_seconds
    return {
        "case_id": case.case_id,
        "lifecycle_complete": case.lifecycle_complete,
        "clearance_seconds": elapsed,
        "within_target": within,
        "economic_measured": bool(case.economic_measured),
        "eligible_for_gate": case.lifecycle_complete and elapsed is not None,
    }


def evaluate_gate(
    *,
    total_cases: int,
    within_two_minutes_rate: float,
    economic_coverage_rate: float,
    thresholds: GateThresholds | None = None,
) -> GateDecision:
    """Evaluate the 90-day production decision from observed durable KPIs."""
    t = thresholds or GateThresholds()

    if total_cases < t.minimum_cases:
        return GateDecision.CONDITIONAL_GO

    if (
        within_two_minutes_rate >= t.go_clearance_rate
        and economic_coverage_rate >= t.go_economic_coverage
    ):
        return GateDecision.GO

    if (
        within_two_minutes_rate >= t.conditional_clearance_rate
        and economic_coverage_rate >= t.conditional_economic_coverage
    ):
        return GateDecision.CONDITIONAL_GO

    return GateDecision.NO_GO


def build_command_summary(
    *,
    total_cases: int,
    within_two_minutes_rate: float,
    average_clearance_seconds: float | None,
    median_clearance_seconds: float | None,
    total_time_saved_minutes: float,
    total_savings_mnt: float,
    economic_measurement_cases: int,
    economic_coverage_rate: float,
    thresholds: GateThresholds | None = None,
) -> dict:
    """Build the compact command result used by a dashboard/API adapter."""
    t = thresholds or GateThresholds()
    decision = evaluate_gate(
        total_cases=total_cases,
        within_two_minutes_rate=within_two_minutes_rate,
        economic_coverage_rate=economic_coverage_rate,
        thresholds=t,
    )
    per_case = (
        total_savings_mnt / economic_measurement_cases
        if economic_measurement_cases
        else None
    )
    return {
        "decision": decision.value,
        "decision_code": decision.name,
        "gate": {
            "target_seconds": t.target_seconds,
            "minimum_cases": t.minimum_cases,
            "go_clearance_rate": t.go_clearance_rate,
            "go_economic_coverage": t.go_economic_coverage,
            "conditional_clearance_rate": t.conditional_clearance_rate,
            "conditional_economic_coverage": t.conditional_economic_coverage,
        },
        "observed": {
            "total_cases": total_cases,
            "within_two_minutes_rate": within_two_minutes_rate,
            "average_clearance_seconds": average_clearance_seconds,
            "median_clearance_seconds": median_clearance_seconds,
            "total_time_saved_minutes": total_time_saved_minutes,
            "economic_measurement_cases": economic_measurement_cases,
            "economic_coverage_rate": economic_coverage_rate,
            "total_savings_mnt": total_savings_mnt,
            "average_savings_per_economic_case_mnt": per_case,
        },
        "one_line": (
            f"{total_cases} case → "
            f"{within_two_minutes_rate:.1%} ≤120 сек → "
            f"{total_time_saved_minutes:.1f} минут хэмнэв → "
            f"{total_savings_mnt:,.0f} ₮ хэмжигдсэн өгөөж → "
            f"{decision.value}"
        ),
    }


def summarize_cases(cases: Iterable[CaseRecord], *, target_seconds: float = 120.0) -> Mapping[str, int | float]:
    """Produce deterministic case-level counts for adapters and tests."""
    rows = list(cases)
    measured = [c for c in rows if c.clearance_seconds is not None]
    within = [c for c in measured if c.clearance_seconds <= target_seconds]
    economic = [c for c in rows if c.economic_measured]
    return {
        "total_cases": len(rows),
        "measured_clearance_cases": len(measured),
        "within_two_minutes_cases": len(within),
        "within_two_minutes_rate": len(within) / len(measured) if measured else 0.0,
        "economic_measurement_cases": len(economic),
        "economic_coverage_rate": len(economic) / len(rows) if rows else 0.0,
    }
