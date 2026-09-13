"""Outbound application API for the EXIM Escrow Port."""

from typing import Any, Dict, Optional

from .contract import ExportedAudit, ExportedSettlement, ExportedStatus, EXIM_PORT_VERSION


class ExternalPortExport:
    """Stable outbound surface; callers receive boundary DTOs only."""

    @staticmethod
    def status(*, status: str, reference_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> ExportedStatus:
        return ExportedStatus(
            port_version=EXIM_PORT_VERSION,
            status=status,
            reference_id=reference_id,
            data=dict(data or {}),
        )

    def escrow_status(self, escrow: Any) -> ExportedStatus:
        state = escrow.get_state()
        return self.status(status=state.get("state", "UNKNOWN"), reference_id=state.get("escrow_id"), data=state)

    def settlement_status(self, escrow: Any) -> ExportedSettlement:
        state = escrow.get_state()
        return ExportedSettlement(
            port_version=EXIM_PORT_VERSION,
            escrow_id=str(state.get("escrow_id", "")),
            status=str(state.get("state", "UNKNOWN")),
            amount=int(getattr(escrow, "amount", 0)),
            currency=str(getattr(escrow, "currency", "MNT")),
            settlement_provider=str(state.get("settlement_provider", "NEF")),
            reference_id=state.get("escrow_id"),
            evidence=dict(state.get("evidence", {}) or {}),
        )

    def witness_status(self, witness: Any) -> ExportedStatus:
        return self.status(
            status="ACTIVE",
            reference_id=getattr(witness, "witness_id", None),
            data={"entry_count": len(getattr(witness, "entries", [])), "current_state_hash": getattr(witness, "current_state_hash", None)},
        )

    def audit_event(self, *, reference_id: str, event_type: str, timestamp: str,
                    evidence_hash: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> ExportedAudit:
        return ExportedAudit(
            port_version=EXIM_PORT_VERSION,
            reference_id=reference_id,
            event_type=event_type,
            timestamp=timestamp,
            evidence_hash=evidence_hash,
            data=dict(data or {}),
        )
