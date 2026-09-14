"""SHUUD sandbox case intake API.

This adapter binds an existing canonical incident to one active sandbox.
It does not create a second lifecycle, witness chain, or escrow engine.
"""

from __future__ import annotations

from datetime import date
import os

from fastapi import APIRouter, HTTPException

from .case_intake import validate_case_intake
from .persistence import SHUUDPersistence
from .sandbox_config import SandboxConfig

router = APIRouter(prefix="/api/v1/shuud/sandbox", tags=["SHUUD Sandbox Intake"])

_PERSISTENCE = SHUUDPersistence(
    os.getenv("SHUUD_PERSISTENCE_URL", "sqlite:///./gerchain.db")
)


@router.post("/config/{sandbox_id}/cases/{incident_id}", response_model=dict)
def intake_sandbox_case(sandbox_id: str, incident_id: str):
    """Bind an existing canonical incident to the active sandbox window."""
    value = _PERSISTENCE.load_sandbox_config(sandbox_id)
    if value is None:
        raise HTTPException(status_code=404, detail="SANDBOX_NOT_FOUND")
    config = SandboxConfig.from_dict(value)

    expected_snapshot = _PERSISTENCE.load_snapshot(incident_id)
    if expected_snapshot is None:
        raise HTTPException(status_code=404, detail="INCIDENT_NOT_FOUND")

    existing = expected_snapshot.get("sandbox_case")
    if isinstance(existing, dict) and existing.get("sandbox_id") != sandbox_id:
        raise HTTPException(
            status_code=409,
            detail="CASE_ALREADY_BOUND_TO_OTHER_SANDBOX",
        )

    try:
        binding = validate_case_intake(
            config,
            incident_id=incident_id,
            intake_date=date.today(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    binding_data = binding.to_dict()
    if existing == binding_data:
        return {
            "status": "success",
            "binding": binding_data,
            "persisted": True,
            "idempotent": True,
        }

    updated = dict(expected_snapshot)
    updated["sandbox_case"] = binding_data
    if not _PERSISTENCE.save_snapshot_if_current(
        incident_id,
        expected_snapshot,
        updated,
    ):
        raise HTTPException(status_code=409, detail="SHUUD_STATE_CONFLICT")

    return {
        "status": "success",
        "binding": binding_data,
        "persisted": True,
        "idempotent": False,
    }


@router.get("/config/{sandbox_id}/cases/{incident_id}", response_model=dict)
def get_sandbox_case(sandbox_id: str, incident_id: str):
    """Read the durable sandbox binding without changing lifecycle state."""
    value = _PERSISTENCE.load_sandbox_config(sandbox_id)
    if value is None:
        raise HTTPException(status_code=404, detail="SANDBOX_NOT_FOUND")
    snapshot = _PERSISTENCE.load_snapshot(incident_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="INCIDENT_NOT_FOUND")
    binding = snapshot.get("sandbox_case")
    if not isinstance(binding, dict) or binding.get("sandbox_id") != sandbox_id:
        raise HTTPException(status_code=404, detail="SANDBOX_CASE_NOT_FOUND")
    return {"status": "success", "binding": binding, "persisted": True}


__all__ = ["router"]
