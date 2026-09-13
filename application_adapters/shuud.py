"""SHUUD application adapter.

SHUUD talks to the controlled gateway only. It has no dependency on the
EXIM Port package, NEF, GerChain engines, or their internal DTOs.

Every application-to-gateway operation carries the connector credential and a
fresh request nonce. The application adapter never bypasses gateway governance.
"""

from typing import Any

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

    def _dispatch(self, operation: str, *, nonce: str, **kwargs: Any) -> Any:
        return self.gateway.dispatch(
            self.connector_id,
            operation,
            credential=self.credential,
            nonce=nonce,
            **kwargs,
        )

    def create_witness_chain(self, *, nonce: str, initial_state: dict[str, Any], manifest: dict[str, Any], witness_id: str, initial_money_state: dict[str, Any] | None = None) -> Any:
        return self._dispatch("create_witness_chain", nonce=nonce, initial_state=initial_state, manifest=manifest, witness_id=witness_id, initial_money_state=initial_money_state)

    def restore_witness_chain(self, bundle: dict[str, Any], *, nonce: str) -> Any:
        return self._dispatch("restore_witness_chain", nonce=nonce, bundle=bundle)

    def create_escrow(self, *, nonce: str, escrow_id: str, amount: int, currency: str, settlement_provider: str, witness_chain: Any) -> Any:
        return self._dispatch("create_escrow", nonce=nonce, escrow_id=escrow_id, amount=amount, currency=currency, settlement_provider=settlement_provider, witness_chain=witness_chain)

    def restore_escrow(self, *, nonce: str, escrow_id: str, amount: int, currency: str, state: dict[str, Any], records: list[dict[str, Any]], witness_chain: Any) -> Any:
        return self._dispatch("restore_escrow", nonce=nonce, escrow_id=escrow_id, amount=amount, currency=currency, state=state, records=records, witness_chain=witness_chain)

    def verifier(self, *, nonce: str) -> Any:
        return self._dispatch("verifier", nonce=nonce)

    def release_escrow(self, escrow: Any, *, nonce: str, **kwargs: Any) -> Any:
        return self._dispatch("release_escrow", nonce=nonce, escrow=escrow, **kwargs)

    def release_escrow_authorized(self, escrow: Any, *, nonce: str, **kwargs: Any) -> Any:
        return self._dispatch("release_escrow_authorized", nonce=nonce, escrow=escrow, **kwargs)

    def export_status(self, *, nonce: str, **kwargs: Any) -> Any:
        return self._dispatch("export_status", nonce=nonce, **kwargs)

    def export_escrow_status(self, *, nonce: str, **kwargs: Any) -> Any:
        return self._dispatch("export_escrow_status", nonce=nonce, **kwargs)

    def export_settlement(self, *, nonce: str, **kwargs: Any) -> Any:
        return self._dispatch("export_settlement_status", nonce=nonce, **kwargs)

    def export_evidence(self, *, nonce: str, **kwargs: Any) -> Any:
        return self._dispatch("export_evidence_status", nonce=nonce, **kwargs)

    def export_audit(self, *, nonce: str, **kwargs: Any) -> Any:
        return self._dispatch("export_audit_event", nonce=nonce, **kwargs)


__all__ = ["EXIM_OPERATIONS", "SHUUDApplicationAdapter"]
