from datetime import datetime, timezone
from typing import List
from uuid import uuid4
import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from database.db import get_connection, log_transition

router = APIRouter(prefix="/api/shuud", tags=["SHUUD"])

class IncidentCreate(BaseModel):
    location: str = Field(min_length=2, max_length=240)
    amount: float = Field(gt=0, le=2_000_000)
    description: str = Field(default="Жижиг замын тохиолдол", max_length=500)

class IncidentDecision(BaseModel):
    approved: bool
    actor: str = "SHIID"

class IncidentAction(BaseModel):
    actor: str = "SHUUD"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_shuud_db() -> None:
    conn = get_connection()
    conn.execute("""CREATE TABLE IF NOT EXISTS shuud_incidents (
        id TEXT PRIMARY KEY, location TEXT NOT NULL, amount REAL NOT NULL,
        description TEXT NOT NULL, state TEXT NOT NULL, started_at TEXT NOT NULL,
        updated_at TEXT NOT NULL, escrow_id TEXT NOT NULL UNIQUE)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS shuud_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL,
        state TEXT NOT NULL, actor TEXT NOT NULL, at TEXT NOT NULL,
        FOREIGN KEY (incident_id) REFERENCES shuud_incidents(id))""")
    conn.commit(); conn.close()

init_shuud_db()


def _row(conn, incident_id):
    return conn.execute("SELECT * FROM shuud_incidents WHERE id = ?", (incident_id,)).fetchone()


def _public(conn, row):
    events = conn.execute("SELECT state, actor, at FROM shuud_events WHERE incident_id = ? ORDER BY id", (row["id"],)).fetchall()
    return dict(row) | {"events": [dict(e) for e in events]}


def _event(conn, incident_id, state, actor, at):
    conn.execute("INSERT INTO shuud_events (incident_id, state, actor, at) VALUES (?, ?, ?, ?)", (incident_id, state, actor, at))


def _escrow_create(item):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO escrows (id, sender_address, receiver_address, amount, state, condition_desc) VALUES (?, ?, ?, ?, 'CREATED', ?)",
                     (item["escrow_id"], "SHUUD_INSURER", "DRIVER", item["amount"], "SHIID approval + road clearance"))
        conn.commit()
    finally:
        conn.close()
    log_transition(item["escrow_id"], "NONE", "CREATED", "SHUUD")


def _escrow_action(escrow_id, action, actor):
    conn = get_connection()
    try:
        row = conn.execute("SELECT state FROM escrows WHERE id = ?", (escrow_id,)).fetchone()
        if not row: raise HTTPException(500, "SHUUD escrow олдсонгүй")
        current = row["state"]
        target = "LOCKED" if action == "LOCK" else "RELEASED"
        expected = "CREATED" if action == "LOCK" else "LOCKED"
        if current != expected: raise HTTPException(409, f"Escrow төлөв буруу: {current} -> {action}")
        conn.execute("UPDATE escrows SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (target, escrow_id))
        conn.commit()
    finally:
        conn.close()
    log_transition(escrow_id, current, target, actor)


@router.post("/incidents")
def create_incident(data: IncidentCreate):
    incident_id = f"SH-{datetime.now().strftime('%y%m%d')}-{uuid4().hex[:4].upper()}"
    escrow_id = f"ESC-{incident_id}"
    at = now_iso()
    item = {"id": incident_id, "location": data.location, "amount": data.amount, "description": data.description,
            "state": "REPORTED", "started_at": at, "updated_at": at, "escrow_id": escrow_id}
    conn = get_connection()
    try:
        conn.execute("INSERT INTO shuud_incidents (id, location, amount, description, state, started_at, updated_at, escrow_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tuple(item.values()))
        _event(conn, incident_id, "REPORTED", "DRIVER", at); conn.commit()
    except sqlite3.IntegrityError:
        conn.close(); raise HTTPException(409, "Тохиолдлын ID давхардлаа")
    conn.close(); _escrow_create(item)
    return {**item, "events": [{"state": "REPORTED", "actor": "DRIVER", "at": at}]}


@router.get("/incidents")
def list_incidents() -> List[dict]:
    conn = get_connection(); rows = conn.execute("SELECT * FROM shuud_incidents ORDER BY started_at DESC").fetchall()
    result = [_public(conn, r) for r in rows]; conn.close(); return result


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    conn = get_connection(); row = _row(conn, incident_id)
    if not row: conn.close(); raise HTTPException(404, "Тохиолдол олдсонгүй")
    result = _public(conn, row); conn.close(); return result


def _transition(incident_id, expected, new_state, actor, lock=False, release=False):
    conn = get_connection(); row = _row(conn, incident_id)
    if not row: conn.close(); raise HTTPException(404, "Тохиолдол олдсонгүй")
    if row["state"] != expected:
        conn.close(); raise HTTPException(409, f"Буруу төлөв шилжилт: {row['state']} -> {new_state}")
    at = now_iso(); conn.execute("UPDATE shuud_incidents SET state = ?, updated_at = ? WHERE id = ?", (new_state, at, incident_id))
    _event(conn, incident_id, new_state, actor, at); conn.commit()
    result = _public(conn, _row(conn, incident_id)); conn.close()
    if lock: _escrow_action(row["escrow_id"], "LOCK", actor)
    if release: _escrow_action(row["escrow_id"], "RELEASE", actor)
    return result


@router.post("/incidents/{incident_id}/evidence")
def verify_evidence(incident_id: str, data: IncidentAction):
    return _transition(incident_id, "REPORTED", "EVIDENCE_VERIFIED", data.actor)

@router.post("/incidents/{incident_id}/decision")
def decide_incident(incident_id: str, data: IncidentDecision):
    return _transition(incident_id, "EVIDENCE_VERIFIED", "SHIID_APPROVED" if data.approved else "REJECTED", data.actor, lock=data.approved)

@router.post("/incidents/{incident_id}/clearance")
def clear_incident(incident_id: str, data: IncidentAction):
    return _transition(incident_id, "SHIID_APPROVED", "CLEARED", data.actor)

@router.post("/incidents/{incident_id}/payment")
def release_payment(incident_id: str, data: IncidentAction):
    return _transition(incident_id, "CLEARED", "PAYMENT_RELEASED", data.actor, release=True)
