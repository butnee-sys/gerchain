"""Tamper-evident audit records for DEE authorization decisions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


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


def _record_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def append_record(
    *,
    sequence: int,
    event: str,
    change_id: str,
    owner_id: str,
    decision: str,
    previous_hash: str = "GENESIS",
) -> AuditRecord:
    if sequence < 1:
        raise ValueError("sequence must be positive")
    timestamp = datetime.now(timezone.utc).isoformat()
    payload = {
        "sequence": sequence,
        "timestamp": timestamp,
        "event": event,
        "change_id": change_id,
        "owner_id": owner_id,
        "decision": decision,
        "previous_hash": previous_hash,
    }
    return AuditRecord(
        **payload,
        record_hash=_record_hash(payload),
    )


def verify_chain(records: list[AuditRecord]) -> bool:
    previous = "GENESIS"
    for expected_sequence, record in enumerate(records, start=1):
        if record.sequence != expected_sequence or record.previous_hash != previous:
            return False
        payload = {
            "sequence": record.sequence,
            "timestamp": record.timestamp,
            "event": record.event,
            "change_id": record.change_id,
            "owner_id": record.owner_id,
            "decision": record.decision,
            "previous_hash": record.previous_hash,
        }
        if _record_hash(payload) != record.record_hash:
            return False
        previous = record.record_hash
    return True
