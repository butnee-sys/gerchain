"""SHUUD 90-day sandbox decision API.

This is a read-only decision adapter over durable KPI measurements. It does not
create incidents, alter SHIID decisions, authorize releases, or write economic
measurements.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from .command_layer import build_command_summary
from .kpi_api import _aggregate

router = APIRouter(prefix="/api/v1/shuud/sandbox", tags=["SHUUD Sandbox Command"])


def _command(start_at: datetime | None = None) -> dict:
    kpi = _aggregate(start_at)
    result = build_command_summary(
        total_cases=int(kpi["total_cases"]),
        within_two_minutes_rate=float(kpi["within_two_minutes_rate"]),
        average_clearance_seconds=kpi["average_clearance_seconds"],
        median_clearance_seconds=kpi["median_clearance_seconds"],
        total_time_saved_minutes=float(kpi["total_time_saved_minutes"]),
        total_savings_mnt=float(kpi["total_savings_mnt"]),
        economic_measurement_cases=int(kpi["economic_measurement_cases"]),
        economic_coverage_rate=float(kpi["economic_coverage_rate"]),
    )
    result["kpi"] = kpi
    return result


@router.get("/command", response_model=dict)
def get_sandbox_command():
    return _command()


@router.get("/command/daily", response_model=dict)
def get_daily_sandbox_command():
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return _command(start)


@router.get("/command/weekly", response_model=dict)
def get_weekly_sandbox_command():
    return _command(datetime.now(timezone.utc) - timedelta(days=7))


__all__ = ["router"]
