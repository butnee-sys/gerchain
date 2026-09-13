from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/shuud", tags=["SHUUD"])

INCIDENTS: Dict[str, dict] = {}

STAGES = [
    "REPORTED",
    "EVIDENCE_VERIFIED",
    "SHIID_APPROVED",
    "CLEARANCE_READY",
    "CLEARED",
    "PAYMENT_RELEASED",
]

class IncidentCreate(BaseModel):
    location: str
    amount: float = Field(gt=0, le=2_000_000)
    description: str = "Жижиг замын тохиолдол"

class IncidentDecision(BaseModel):
    approved: bool
    actor: str = "SHIID"

class IncidentAction(BaseModel):
    actor: str = "SHUUD"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def public_incident(x: dict) -> dict:
    return {k: v for k, v in x.items() if k != "events"} | {"events": x["events"]}


@router.post("/incidents")
def create_incident(data: IncidentCreate):
    incident_id = f"SH-{datetime.now().strftime('%y%m%d')}-{uuid4().hex[:4].upper()}"
    item = {
        "id": incident_id,
        "location": data.location,
        "amount": data.amount,
        "description": data.description,
        "state": "REPORTED",
        "started_at": now_iso(),
        "updated_at": now_iso(),
        "escrow_id": f"ESC-{incident_id}",
        "events": [{"state": "REPORTED", "at": now_iso(), "actor": "DRIVER"}],
    }
    INCIDENTS[incident_id] = item
    return public_incident(item)


@router.get("/incidents")
def list_incidents() -> List[dict]:
    return [public_incident(x) for x in INCIDENTS.values()]


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    item = INCIDENTS.get(incident_id)
    if not item:
        raise HTTPException(404, "Тохиолдол олдсонгүй")
    return public_incident(item)


@router.post("/incidents/{incident_id}/evidence")
def verify_evidence(incident_id: str, data: IncidentAction):
    item = INCIDENTS.get(incident_id)
    if not item:
        raise HTTPException(404, "Тохиолдол олдсонгүй")
    if item["state"] != "REPORTED":
        raise HTTPException(409, "Evidence энэ төлөвт баталгаажихгүй")
    at = now_iso()
    item["state"] = "EVIDENCE_VERIFIED"
    item["updated_at"] = at
    item["events"].append({"state": item["state"], "at": at, "actor": data.actor})
    return public_incident(item)


@router.post("/incidents/{incident_id}/decision")
def decide_incident(incident_id: str, data: IncidentDecision):
    item = INCIDENTS.get(incident_id)
    if not item:
        raise HTTPException(404, "Тохиолдол олдсонгүй")
    if item["state"] != "EVIDENCE_VERIFIED":
        raise HTTPException(409, "SHIID шийдвэрийн өмнө Evidence баталгаажсан байх ёстой")
    if not data.approved:
        item["state"] = "REJECTED"
    else:
        item["state"] = "SHIID_APPROVED"
    at = now_iso()
    item["updated_at"] = at
    item["events"].append({"state": item["state"], "at": at, "actor": data.actor})
    return public_incident(item)


@router.post("/incidents/{incident_id}/clearance")
def clear_incident(incident_id: str, data: IncidentAction):
    item = INCIDENTS.get(incident_id)
    if not item:
        raise HTTPException(404, "Тохиолдол олдсонгүй")
    if item["state"] != "SHIID_APPROVED":
        raise HTTPException(409, "Зам чөлөөлөхийн өмнө SHIID баталгаажсан байх ёстой")
    at = now_iso()
    item["state"] = "CLEARED"
    item["updated_at"] = at
    item["events"].append({"state": item["state"], "at": at, "actor": data.actor})
    return public_incident(item)


@router.post("/incidents/{incident_id}/payment")
def release_payment(incident_id: str, data: IncidentAction):
    item = INCIDENTS.get(incident_id)
    if not item:
        raise HTTPException(404, "Тохиолдол олдсонгүй")
    if item["state"] != "CLEARED":
        raise HTTPException(409, "Төлбөрийг зам чөлөөлсний дараа гаргана")
    at = now_iso()
    item["state"] = "PAYMENT_RELEASED"
    item["updated_at"] = at
    item["events"].append({"state": item["state"], "at": at, "actor": data.actor})
    return public_incident(item)
