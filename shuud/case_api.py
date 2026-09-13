"""Read-only SHUUD case view for operator and mobile clients."""

from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException

from .persistence import SHUUDPersistence

router = APIRouter(prefix="/api/v1/shuud", tags=["SHUUD Case"])
_PERSISTENCE = SHUUDPersistence(os.getenv("SHUUD_PERSISTENCE_URL", "sqlite:///./gerchain.db"))


def _state(snapshot: dict) -> str:
    if snapshot.get("economic_measurement"):
        return "complete"
    timing = snapshot.get("operational_timing") or {}
    if timing.get("clearance_confirmed_at"):
        return "clearance"
    escrow = snapshot.get("escrow") or {}
    escrow_state = (escrow.get("state") or {}).get("state")
    if escrow_state == "RELEASED":
        return "release"
    if escrow:
        return "escrow"
    if snapshot.get("decision"):
        return "decision"
    if snapshot.get("evidence"):
        return "evidence"
    return "incident"


@router.get("/incidents/{incident_id}", response_model=dict)
def get_shuud_case(incident_id: str):
    snapshot = _PERSISTENCE.load_snapshot(incident_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="INCIDENT_NOT_FOUND")

    incident = snapshot.get("incident") or {}
    evidence = snapshot.get("evidence") or {}
    decision = snapshot.get("decision") or {}
    escrow = snapshot.get("escrow") or {}
    timing = snapshot.get("operational_timing") or {}
    economic = snapshot.get("economic_measurement") or {}
    escrow_state = escrow.get("state") or {}

    return {
        "status": "success",
        "incident_id": incident_id,
        "state": _state(snapshot),
        "location": incident.get("location"),
        "vehicle_a": incident.get("vehicle_a"),
        "vehicle_b": incident.get("vehicle_b"),
        "description": incident.get("description"),
        "decision": decision.get("decision"),
        "rule_version": decision.get("rule_version"),
        "insurance": "VALID" if decision.get("decision") == "APPROVE" else None,
        "evidence_locked": bool(evidence),
        "escrow_id": escrow.get("escrow_id"),
        "escrow_state": escrow_state.get("state"),
        "payment": "RELEASED" if escrow_state.get("state") == "RELEASED" else None,
        "provider": escrow.get("settlement_provider") or "NEF",
        "clearance_seconds": (
            timing.get("durations", {}).get("incident_created_at_to_clearance_confirmed_at")
        ),
        "milestones": timing,
        "economic_savings_mnt": economic.get("total_savings_mnt"),
        "economic_measurement": economic or None,
    }


__all__ = ["router"]
