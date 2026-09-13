"""SHUUD application adapter.

SHUUD talks to the controlled gateway only. It has no dependency on the
EXIM Port package, NEF, GerChain engines, or their internal DTOs.
"""

from typing import Any

from connectors import EXIMConnectorAdapter
from gateway import OpenMultiConnectorGateway


class SHUUDApplicationAdapter:
    """Translate SHUUD domain operations into gateway operations."""

    application_id = "SHUUD"
    connector_id = "EXIM"

    def __init__(self, gateway: OpenMultiConnectorGateway | None = None) -> None:
        self.gateway = gateway or OpenMultiConnectorGateway()
        if self.connector_id not in self.gateway.registered_connectors():
            self.gateway.register(EXIMConnectorAdapter())

    def create_witness_chain(
        self,
        *,
        initial_state: dict[str, Any],
        manifest: dict[str, Any],
        witness_id: str,
        initial_money_state: dict[str, Any] | None = None,
    ) -> Any:
        return self.gateway.dispatch(
            self.connector_id,
            "create_witness_chain",
            initial_state=initial_state,
            manifest=manifest,
            witness_id=witness_id,
            initial_money_state=initial_money_state,
        )

    def release_escrow(self, escrow: Any, **kwargs: Any) -> Any:
        return self.gateway.dispatch(
            self.connector_id,
            "release_escrow",
            escrow=escrow,
            **kwargs,
        )

    def release_escrow_authorized(self, escrow: Any, **kwargs: Any) -> Any:
        return self.gateway.dispatch(
            self.connector_id,
            "release_escrow_authorized",
            escrow=escrow,
            **kwargs,
        )

    def export_evidence(self, **kwargs: Any) -> Any:
        return self.gateway.dispatch(self.connector_id, "export_evidence_status", **kwargs)

    def export_audit(self, **kwargs: Any) -> Any:
        return self.gateway.dispatch(self.connector_id, "export_audit_event", **kwargs)


__all__ = ["SHUUDApplicationAdapter"]
