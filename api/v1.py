from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from database.db import get_connection, log_transition

router = APIRouter(prefix="/api/v1", tags=["Fintech API"])\n\n# Legacy SQLite mutation surface is not a production value/state authority.\nLEGACY_MUTATION_DISABLED = True

class EscrowCreateRequest(BaseModel):
    escrow_id: str
    sender_address: str
    receiver_address: str
    amount: float
    condition_desc: str

class ActionRequest(BaseModel):
    action: str # LOCK or RELEASE
    actor: str

@router.post("/escrows/create")
def api_create_escrow(data: EscrowCreateRequest):\n    if LEGACY_MUTATION_DISABLED:\n        raise HTTPException(status_code=410, detail="Legacy SQLite escrow mutation is disabled; use the production runtime boundary.")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO escrows (id, sender_address, receiver_address, amount, state, condition_desc) VALUES (?, ?, ?, ?, 'CREATED', ?)",
            (data.escrow_id, data.sender_address, data.receiver_address, data.amount, data.condition_desc)
        )
        conn.commit()
        log_transition(data.escrow_id, "NONE", "CREATED", "API_FINTECH_CLIENT")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

    conn.close()
    return {"status": "success", "escrow_id": data.escrow_id, "state": "CREATED"}

@router.get("/escrows/{escrow_id}")
def api_get_escrow(escrow_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM escrows WHERE id = ?", (escrow_id,))
    escrow = cursor.fetchone()
    conn.close()

    if not escrow:
        raise HTTPException(status_code=404, detail="Эскроу гэрээ олдсонгүй")

    return {
        "escrow_id": escrow["id"],
        "sender": escrow["sender_address"],
        "receiver": escrow["receiver_address"],
        "amount": escrow["amount"],
        "state": escrow["state"],
        "condition": escrow["condition_desc"],
        "updated_at": escrow["updated_at"]
    }

@router.post("/escrows/{escrow_id}/action")
def api_escrow_action(escrow_id: str, data: ActionRequest):\n    if LEGACY_MUTATION_DISABLED:\n        raise HTTPException(status_code=410, detail="Legacy direct escrow mutation is disabled; use the production runtime boundary.")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM escrows WHERE id = ?", (escrow_id,))
    escrow = cursor.fetchone()

    if not escrow:
        conn.close()
        raise HTTPException(status_code=404, detail="Эскроу гэрээ олдсонгүй")

    current_state = escrow["state"]
    action = data.action.upper()
    new_state = ""

    if action == "LOCK" and current_state == "CREATED":
        new_state = "LOCKED"
    elif action == "RELEASE" and current_state == "LOCKED":
        new_state = "RELEASED"
    else:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Буруу төлөв шилжилт: {current_state} -> {action}")

    cursor.execute("UPDATE escrows SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_state, escrow_id))
    conn.commit()
    log_transition(escrow_id, current_state, new_state, data.actor)
    conn.close()

    return {"status": "success", "escrow_id": escrow_id, "previous_state": current_state, "new_state": new_state}
