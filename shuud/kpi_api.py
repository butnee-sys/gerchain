"""Durable SHUUD sandbox KPI and economic measurement read/write API.

The economic endpoint persists only explicit caller-supplied assumptions and the
observed clearance result. Canonical incident, WitnessChain and EscrowEngine state
remains owned by the existing SHUUD persistence/runtime paths.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from .measurement_summary import build_measurement_summary
from .metrics import OperationalTiming
from .persistence import SHUUDPersistence, SHUUDStateRow

router = APIRouter(prefix="/api/v1/shuud/sandbox", tags=["SHUUD Sandbox KPI"])

_PERSISTENCE = SHUUDPersistence(
    os.getenv("SHUUD_PERSISTENCE_URL", "sqlite:///./gerchain.db")
)

ECONOMIC_MODEL_VERSION = "shuud-economic-v1"
DEFAULT_TARGET_SECONDS = 120.0


class EconomicMeasurementRequest(BaseModel):
    baseline_seconds: float = Field(ge=0)
    affected_vehicles: int = Field(ge=1)
    vehicle_value_per_minute_mnt: float = Field(ge=0)
    insurer_cost_per_minute_mnt: float = Field(default=0.0, ge=0)
    public_road_cost_per_minute_mnt: float = Field(default=0.0, ge=0)


def _rows(start_at: datetime | None = None) -> list[dict[str, Any]]:
    with _PERSISTENCE.SessionLocal() as session:
        rows = list(session.execute(select(SHUUDStateRow)).scalars())

    start_iso = start_at.astimezone(timezone.utc).isoformat() if start_at else None
    snapshots: list[dict[str, Any]] = []
    for row in rows:
        snapshot = json.loads(row.snapshot_json)
        recorded = snapshot.get("operational_timing", {}).get("incident_created_at")
        if start_iso and (recorded is None or recorded < start_iso):
            continue
        snapshots.append(snapshot)
    return snapshots


def aggregate_snapshots(
    snapshots: list[dict[str, Any]],
    *,
    target_seconds: float = DEFAULT_TARGET_SECONDS,
) -> dict[str, Any]:
    """Aggregate one canonical snapshot per incident without transient-state input.

    ``shuud_state`` is keyed by incident_id, so each snapshot represents one
    authoritative case. Economic values are read only from persisted
    ``shuud-economic-v1`` records; other objects are not counted as economic
    evidence and are never recomputed here.
    """
    clearance: list[float] = []
    approved = 0
    released = 0
    within = 0
    economic = [
        snapshot["economic_measurement"]
        for snapshot in snapshots
        if isinstance(snapshot.get("economic_measurement"), dict)
        and snapshot["economic_measurement"].get("model_version")
        == ECONOMIC_MODEL_VERSION
    ]

    for snapshot in snapshots:
        timing = snapshot.get("operational_timing") or {}
        created = timing.get("incident_created_at")
        cleared = timing.get("clearance_confirmed_at")
        if created and cleared:
            seconds = (
                datetime.fromisoformat(cleared) - datetime.fromisoformat(created)
            ).total_seconds()
            if seconds < 0:
                continue
            clearance.append(seconds)
            if seconds <= target_seconds:
                within += 1

        decision = snapshot.get("decision") or {}
        if decision.get("decision") == "APPROVE":
            approved += 1

        escrow = snapshot.get("escrow") or {}
        escrow_state = escrow.get("state") or {}
        if escrow_state.get("state") == "RELEASED":
            released += 1

    total = len(snapshots)
    measured = len(clearance)
    economic_cases = len(economic)
    total_time_saved_seconds = sum(
        float(item.get("time_saved_seconds", 0.0)) for item in economic
    )
    return {
        "status": "success",
        "scope": "90-day-sandbox",
        "target_seconds": target_seconds,
        "total_cases": total,
        "measured_clearance_cases": measured,
        "within_two_minutes_cases": within,
        "within_two_minutes_rate": within / measured if measured else 0.0,
        "shiid_approved_cases": approved,
        "shiid_approval_rate": approved / total if total else 0.0,
        "release_success_cases": released,
        "release_success_rate": released / total if total else 0.0,
        "average_clearance_seconds": sum(clearance) / measured if measured else None,
        "median_clearance_seconds": median(clearance) if clearance else None,
        "minimum_clearance_seconds": min(clearance) if clearance else None,
        "maximum_clearance_seconds": max(clearance) if clearance else None,
        "economic_measurement_cases": economic_cases,
        "economic_coverage_rate": economic_cases / total if total else 0.0,
        "total_time_saved_seconds": total_time_saved_seconds,
        "total_time_saved_minutes": total_time_saved_seconds / 60.0,
        "total_vehicle_user_savings_mnt": sum(
            float(item.get("vehicle_user_savings_mnt", 0.0)) for item in economic
        ),
        "total_insurer_savings_mnt": sum(
            float(item.get("insurer_savings_mnt", 0.0)) for item in economic
        ),
        "total_public_road_savings_mnt": sum(
            float(item.get("public_road_savings_mnt", 0.0)) for item in economic
        ),
        "total_savings_mnt": sum(
            float(item.get("total_savings_mnt", 0.0)) for item in economic
        ),
    }


def _aggregate(
    start_at: datetime | None = None,
    *,
    target_seconds: float = DEFAULT_TARGET_SECONDS,
) -> dict[str, Any]:
    return aggregate_snapshots(_rows(start_at), target_seconds=target_seconds)


@router.post("/metrics/{incident_id}/economic", response_model=dict)
def persist_economic_measurement(
    incident_id: str,
    payload: EconomicMeasurementRequest,
):
    expected_snapshot = _PERSISTENCE.load_snapshot(incident_id)
    if expected_snapshot is None:
        raise HTTPException(status_code=404, detail="INCIDENT_NOT_FOUND")

    timing = OperationalTiming.from_dict(expected_snapshot.get("operational_timing") or {})
    summary = build_measurement_summary(
        incident_id=incident_id,
        timing=timing,
        baseline_seconds=payload.baseline_seconds,
        affected_vehicles=payload.affected_vehicles,
        vehicle_value_per_minute_mnt=payload.vehicle_value_per_minute_mnt,
        insurer_cost_per_minute_mnt=payload.insurer_cost_per_minute_mnt,
        public_road_cost_per_minute_mnt=payload.public_road_cost_per_minute_mnt,
    )
    economic = summary.economic_impact
    if economic is None:
        raise HTTPException(status_code=422, detail="ECONOMIC_MEASUREMENT_REQUIRED")

    record = {
        "model_version": ECONOMIC_MODEL_VERSION,
        "baseline_seconds": economic.baseline_seconds,
        "actual_clearance_seconds": economic.actual_seconds,
        "time_saved_seconds": economic.time_saved_seconds,
        "affected_vehicles": economic.affected_vehicles,
        "vehicle_value_per_minute_mnt": economic.vehicle_value_per_minute_mnt,
        "insurer_cost_per_minute_mnt": economic.insurer_cost_per_minute_mnt,
        "public_road_cost_per_minute_mnt": economic.public_road_cost_per_minute_mnt,
        "vehicle_user_savings_mnt": economic.vehicle_user_savings_mnt,
        "insurer_savings_mnt": economic.insurer_savings_mnt,
        "public_road_savings_mnt": economic.public_road_savings_mnt,
        "total_savings_mnt": economic.total_savings_mnt,
    }
    if not _PERSISTENCE.save_economic_measurement_if_current(
        incident_id,
        expected_snapshot,
        record,
    ):
        raise HTTPException(status_code=409, detail="SHUUD_STATE_CONFLICT")

    return {
        "status": "success",
        "incident_id": incident_id,
        "economic_measurement": record,
        "persisted": True,
    }


@router.get("/kpi", response_model=dict)
def get_sandbox_kpi():
    return _aggregate()


@router.get("/kpi/daily", response_model=dict)
def get_daily_sandbox_kpi():
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return _aggregate(start)


@router.get("/kpi/weekly", response_model=dict)
def get_weekly_sandbox_kpi():
    return _aggregate(datetime.now(timezone.utc) - timedelta(days=7))


__all__ = ["aggregate_snapshots", "router"]
