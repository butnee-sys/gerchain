"""Tamper-evident unified audit records for DEE authorization decisions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class AuditRecord:
    sequence: int
    timestamp: str
    event: str
    change_id: str
    owner_id: str
    decision: str
    previous_hash: str
    record_hash: str
    stage: str = "GOVERNANCE"
    connector_id: str = ""
    request_id: str = ""
    operation: str = ""
    trinity: Mapping[str, bool] = None
    witness_state_root: str = ""
    settlement_hash: str = ""
    recovery_decision_hash: str = ""
    execution_chain_hash: str = ""


def _record_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def append_record(*, sequence: int, event: str, change_id: str, owner_id: str, decision: str,
                  previous_hash: str = "GENESIS", stage: str = "GOVERNANCE", connector_id: str = "",
                  request_id: str = "", operation: str = "", trinity: Mapping[str, bool] | None = None,
                  witness_state_root: str = "", settlement_hash: str = "",
                  recovery_decision_hash: str = "", execution_chain_hash: str = "") -> AuditRecord:
    if sequence < 1:
        raise ValueError("sequence must be positive")
    if decision not in {"ALLOW", "DENY"}:
        raise ValueError("decision must be ALLOW or DENY")
    if stage == "SETTLEMENT" and not witness_state_root:
        raise ValueError("settlement audit requires verified witness state root")
    if stage == "RECOVERY" and not all((witness_state_root, settlement_hash, recovery_decision_hash)):
        raise ValueError("recovery audit requires witness, settlement and recovery proof hashes")
    if stage == "RELEASE" and not all((witness_state_root, settlement_hash, recovery_decision_hash, execution_chain_hash)):
        raise ValueError("release audit requires complete execution proof context")
    timestamp = datetime.now(timezone.utc).isoformat()
    proof = dict(trinity or {"trust": True, "transparency": True, "performance": True})
    if set(proof) != {"trust", "transparency", "performance"} or not all(isinstance(v, bool) for v in proof.values()):
        raise ValueError("audit record requires complete boolean Trinity proof")
    payload = {
        "sequence": sequence, "timestamp": timestamp, "event": event,
        "change_id": change_id, "owner_id": owner_id, "decision": decision,
        "previous_hash": previous_hash, "stage": stage, "connector_id": connector_id,
        "request_id": request_id, "operation": operation, "trinity": proof,
        "witness_state_root": witness_state_root, "settlement_hash": settlement_hash,
        "recovery_decision_hash": recovery_decision_hash, "execution_chain_hash": execution_chain_hash,
    }
    return AuditRecord(**payload, record_hash=_record_hash(payload))


def verify_chain(records: list[AuditRecord]) -> bool:
    previous = "GENESIS"
    for expected_sequence, record in enumerate(records, start=1):
        if record.sequence != expected_sequence or record.previous_hash != previous:
            return False
        if record.stage == "SETTLEMENT" and not record.witness_state_root:
            return False
        if record.stage == "RECOVERY" and not all((record.witness_state_root, record.settlement_hash, record.recovery_decision_hash)):
            return False
        if record.stage == "RELEASE" and not all((record.witness_state_root, record.settlement_hash, record.recovery_decision_hash, record.execution_chain_hash)):
            return False
        payload = {
            "sequence": record.sequence, "timestamp": record.timestamp, "event": record.event,
            "change_id": record.change_id, "owner_id": record.owner_id, "decision": record.decision,
            "previous_hash": record.previous_hash, "stage": record.stage,
            "connector_id": record.connector_id, "request_id": record.request_id,
            "operation": record.operation, "trinity": dict(record.trinity or {}),
            "witness_state_root": record.witness_state_root, "settlement_hash": record.settlement_hash,
            "recovery_decision_hash": record.recovery_decision_hash, "execution_chain_hash": record.execution_chain_hash,
        }
        if _record_hash(payload) != record.record_hash:
            return False
        previous = record.record_hash
    return True
