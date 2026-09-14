from __future__ import annotations

from dataclasses import dataclass
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.atomic_release import ReleaseEscrow, ReleaseOperation, ReleaseWitness
from persistence.recovery_outbox import OutboxEvent


@dataclass(frozen=True)
class ReconciliationFinding:
    code: str
    severity: str
    message: str
    transaction_id: str | None = None
    escrow_id: str | None = None
    operation_id: int | None = None


@dataclass(frozen=True)
class ReconciliationReport:
    checked_at: datetime
    findings: tuple[ReconciliationFinding, ...]

    @property
    def passed(self) -> bool:
        return not self.findings


def reconcile_release_state(session: Session) -> ReconciliationReport:
    """Fail-closed consistency check for the operating release store.

    The release path treats the escrow, operation, witness and outbox rows as
    one governed transaction. Reconciliation therefore reports any state that
    cannot be proven internally consistent rather than attempting repair.
    """
    findings: list[ReconciliationFinding] = []

    operations = session.execute(select(ReleaseOperation)).scalars().all()
    escrows = {row.escrow_id: row for row in session.execute(select(ReleaseEscrow)).scalars().all()}
    witnesses = {row.transaction_id: row for row in session.execute(select(ReleaseWitness)).scalars().all()}
    outbox = {row.event_id: row for row in session.execute(select(OutboxEvent)).scalars().all()}

    for op in operations:
        escrow = escrows.get(op.escrow_id)
        witness = witnesses.get(op.transaction_id)
        event = outbox.get(f"release:{op.transaction_id}")

        if escrow is None:
            findings.append(ReconciliationFinding("RC-ESCROW-MISSING", "CRITICAL", "operation references a missing escrow", op.transaction_id, op.escrow_id, op.id))
            continue

        if op.state == "COMPLETED":
            if escrow.state != "RELEASED":
                findings.append(ReconciliationFinding("RC-OP-ESCROW-MISMATCH", "CRITICAL", "COMPLETED operation is not backed by RELEASED escrow", op.transaction_id, op.escrow_id, op.id))
            if witness is None or witness.event_type != "RELEASED" or witness.amount != op.amount:
                findings.append(ReconciliationFinding("RC-WITNESS-MISSING", "CRITICAL", "COMPLETED operation lacks matching release witness", op.transaction_id, op.escrow_id, op.id))
            if event is None or event.event_type != "GERCHAIN_RELEASED" or event.aggregate_id != op.transaction_id:
                findings.append(ReconciliationFinding("RC-OUTBOX-MISSING", "CRITICAL", "COMPLETED operation lacks matching release outbox event", op.transaction_id, op.escrow_id, op.id))
            if op.result_json:
                try:
                    result = json.loads(op.result_json)
                except json.JSONDecodeError:
                    findings.append(ReconciliationFinding("RC-RESULT-INVALID", "CRITICAL", "COMPLETED operation has invalid result_json", op.transaction_id, op.escrow_id, op.id))
                else:
                    if result.get("state") != "RELEASED" or result.get("event_id") != f"release:{op.transaction_id}":
                        findings.append(ReconciliationFinding("RC-RESULT-MISMATCH", "CRITICAL", "COMPLETED operation result does not match release evidence", op.transaction_id, op.escrow_id, op.id))
            else:
                findings.append(ReconciliationFinding("RC-RESULT-MISSING", "CRITICAL", "COMPLETED operation has no result_json", op.transaction_id, op.escrow_id, op.id))

        elif op.state == "PROCESSING":
            age_seconds = (datetime.now(timezone.utc) - op.updated_at).total_seconds()
            if age_seconds >= 300:
                findings.append(ReconciliationFinding("RC-STALE-PROCESSING", "CRITICAL", "PROCESSING operation is older than the recovery lease", op.transaction_id, op.escrow_id, op.id))
            if escrow.state == "LOCKED" and (witness is not None or event is not None):
                findings.append(ReconciliationFinding("RC-LOCKED-WITH-EVIDENCE", "CRITICAL", "LOCKED escrow has release evidence", op.transaction_id, op.escrow_id, op.id))
            if escrow.state == "RELEASED" and (witness is None or event is None):
                findings.append(ReconciliationFinding("RC-RELEASED-INCOMPLETE", "CRITICAL", "RELEASED escrow has incomplete operation evidence", op.transaction_id, op.escrow_id, op.id))
        else:
            findings.append(ReconciliationFinding("RC-STATE-UNKNOWN", "CRITICAL", f"unknown release operation state: {op.state}", op.transaction_id, op.escrow_id, op.id))

    for escrow in escrows.values():
        related = [op for op in operations if op.escrow_id == escrow.escrow_id]
        if escrow.state == "RELEASED":
            completed = [op for op in related if op.state == "COMPLETED"]
            if len(completed) != 1:
                findings.append(ReconciliationFinding("RC-ESCROW-COMPLETION-COUNT", "CRITICAL", "RELEASED escrow must have exactly one COMPLETED operation", None, escrow.escrow_id, None))

    for witness in witnesses.values():
        matching = [op for op in operations if op.transaction_id == witness.transaction_id]
        if len(matching) != 1:
            findings.append(ReconciliationFinding("RC-WITNESS-ORPHAN", "CRITICAL", "witness does not map to exactly one release operation", witness.transaction_id, None, None))

    for event in outbox.values():
        if event.event_type != "GERCHAIN_RELEASED":
            continue
        matching = [op for op in operations if op.transaction_id == event.aggregate_id]
        if len(matching) != 1:
            findings.append(ReconciliationFinding("RC-OUTBOX-ORPHAN", "CRITICAL", "release outbox event does not map to exactly one operation", event.aggregate_id, None, None))

    return ReconciliationReport(datetime.now(timezone.utc), tuple(findings))


__all__ = ["ReconciliationFinding", "ReconciliationReport", "reconcile_release_state"]
