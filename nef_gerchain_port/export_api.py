"""Outbound application API for the EXIM Escrow Port."""

from typing import Any, Dict, Optional

from .contract import (
    EXIM_PORT_VERSION,
    ExportedAudit,
    ExportedEvidence,
    ExportedSettlement,
    ExportedStatus,
)


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
        return self.status(
            status=state.get("state", "UNKNOWN"),
            reference_id=state.get("escrow_id"),
            data=state,
        )

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

    def evidence(
        self,
        *,
        evidence_id: str,
        case_id: str,
        evidence_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExportedEvidence:
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("evidence_id must be a non-empty string")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("case_id must be a non-empty string")
        return ExportedEvidence(
            port_version=EXIM_PORT_VERSION,
            evidence_id=evidence_id,
            case_id=case_id,
            evidence_hash=evidence_hash,
            metadata=dict(metadata or {}),
        )

    def witness_status(self, witness: Any) -> ExportedStatus:
        return self.status(
            status="ACTIVE",
            reference_id=getattr(witness, "witness_id", None),
            data={
                "entry_count": len(getattr(witness, "entries", [])),
                "current_state_hash": getattr(witness, "current_state_hash", None),
            },
        )

    def audit_event(
        self,
        *,
        reference_id: str,
        event_type: str,
        timestamp: str,
        evidence_hash: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> ExportedAudit:
        return ExportedAudit(
            port_version=EXIM_PORT_VERSION,
            reference_id=reference_id,
            event_type=event_type,
            timestamp=timestamp,
            evidence_hash=evidence_hash,
            data=dict(data or {}),
        )
