"""Durable SHUUD sandbox KPI read API.

This layer is measurement-only. Canonical incident, WitnessChain and EscrowEngine
state remains owned by the existing SHUUD persistence/runtime paths.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any

from fastapi import APIRouter
from sqlalchemy import select

from .persistence import SHUUDPersistence, SHUUDStateRow

router = APIRouter(prefix="/api/v1/shuud/sandbox", tags=["SHUUD Sandbox KPI"])

_PERSISTENCE = SHUUDPersistence(
    os.getenv("SHUUD_PERSISTENCE_URL", "sqlite:///./gerchain.db")
)


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


def _aggregate(start_at: datetime | None = None) -> dict[str, Any]:
    snapshots = _rows(start_at)
    clearance: list[float] = []
    approved = 0
    released = 0
    within = 0

    for snapshot in snapshots:
        timing = snapshot.get("operational_timing") or {}
        created = timing.get("incident_created_at")
        cleared = timing.get("clearance_confirmed_at")
        if created and cleared:
            seconds = (
                datetime.fromisoformat(cleared) - datetime.fromisoformat(created)
            ).total_seconds()
            clearance.append(seconds)
            if seconds <= 120:
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
    return {
        "status": "success",
        "scope": "90-day-sandbox",
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


__all__ = ["router"]
