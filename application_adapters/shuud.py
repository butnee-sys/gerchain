"""SHUUD application adapter.

SHUUD talks to the controlled gateway only. It has no dependency on the
EXIM Port package, NEF, GerChain engines, or their internal DTOs.

Every application-to-gateway operation carries the connector credential and a
fresh request nonce. The application adapter never bypasses gateway governance.
"""

from typing import Any
from uuid import uuid4

from connectors import EXIMConnectorAdapter
from gateway import OpenMultiConnectorGateway


EXIM_OPERATIONS = frozenset({
    "create_witness_chain",
    "restore_witness_chain",
    "create_escrow",
    "restore_escrow",
    "verifier",
    "release_escrow",
    "release_escrow_authorized",
    "export_status",
    "export_escrow_status",
    "export_settlement_status",
    "export_evidence_status",
    "export_audit_event",
})


class SHUUDApplicationAdapter:
    """Translate SHUUD domain operations into authenticated gateway calls."""

    application_id = "SHUUD"
    connector_id = "EXIM"

    def __init__(self, gateway: OpenMultiConnectorGateway | None = None, *, credential: str) -> None:
        if not str(credential).strip():
            raise ValueError("SHUUD gateway credential is required")
        self.gateway = gateway or OpenMultiConnectorGateway()
        self.credential = credential
        if self.connector_id not in self.gateway.registered_connectors():
            self.gateway.register(
                EXIMConnectorAdapter(),
                credential=credential,
                allowed_operations=EXIM_OPERATIONS,
            )

    @staticmethod
    def _nonce() -> str:
        return f"SHUUD-{uuid4().hex}"

    def _dispatch(self, operation: str, **kwargs: Any) -> Any:
        return self.gateway.dispatch(
            self.connector_id,
            operation,
            credential=self.credential,
            nonce=self._nonce(),
            **kwargs,
        )

    def create_witness_chain(self, *, initial_state: dict[str, Any], manifest: dict[str, Any], witness_id: str, initial_money_state: dict[str, Any] | None = None) -> Any:
        return self._dispatch("create_witness_chain", initial_state=initial_state, manifest=manifest, witness_id=witness_id, initial_money_state=initial_money_state)

    def restore_witness_chain(self, bundle: dict[str, Any]) -> Any:
        return self._dispatch("restore_witness_chain", bundle=bundle)

    def create_escrow(self, *, escrow_id: str, amount: int, currency: str, settlement_provider: str, witness_chain: Any) -> Any:
        return self._dispatch("create_escrow", escrow_id=escrow_id, amount=amount, currency=currency, settlement_provider=settlement_provider, witness_chain=witness_chain)

    def restore_escrow(self, *, escrow_id: str, amount: int, currency: str, state: dict[str, Any], records: list[dict[str, Any]], witness_chain: Any) -> Any:
        return self._dispatch("restore_escrow", escrow_id=escrow_id, amount=amount, currency=currency, state=state, records=records, witness_chain=witness_chain)

    def verifier(self) -> Any:
        return self._dispatch("verifier")

    def release_escrow(self, escrow: Any, **kwargs: Any) -> Any:
        return self._dispatch("release_escrow", escrow=escrow, **kwargs)

    def release_escrow_authorized(self, escrow: Any, **kwargs: Any) -> Any:
        return self._dispatch("release_escrow_authorized", escrow=escrow, **kwargs)

    def export_status(self, **kwargs: Any) -> Any:
        return self._dispatch("export_status", **kwargs)

    def export_escrow_status(self, **kwargs: Any) -> Any:
        return self._dispatch("export_escrow_status", **kwargs)

    def export_settlement(self, **kwargs: Any) -> Any:
        return self._dispatch("export_settlement_status", **kwargs)

    def export_evidence(self, **kwargs: Any) -> Any:
        return self._dispatch("export_evidence_status", **kwargs)

    def export_audit(self, **kwargs: Any) -> Any:
        return self._dispatch("export_audit_event", **kwargs)


__all__ = ["EXIM_OPERATIONS", "SHUUDApplicationAdapter"]
