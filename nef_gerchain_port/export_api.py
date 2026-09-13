"""Outbound application API for the NEF–GerChain external boundary."""

from typing import Any, Dict, Optional

from .contract import ExportedStatus, PORT_VERSION


class ExternalPortExport:
    """Stable read/export surface; callers receive boundary DTOs only."""

    @staticmethod
    def status(
        *,
        status: str,
        reference_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> ExportedStatus:
        return ExportedStatus(
            port_version=PORT_VERSION,
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

    def witness_status(self, witness: Any) -> ExportedStatus:
        return self.status(
            status="ACTIVE",
            reference_id=getattr(witness, "witness_id", None),
            data={
                "entry_count": len(getattr(witness, "entries", [])),
                "current_state_hash": getattr(witness, "current_state_hash", None),
            },
        )
