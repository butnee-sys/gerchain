"""I2B Multi-Connector Gateway.

The Gateway is the routing/governance layer. Concrete connector registration,
authentication and dispatch live in the explicit MultiConnectorAdapter below.
"""

from typing import Any

from .multi_connector_adapter import GatewayAuditEvent, MultiConnectorAdapter


class OpenMultiConnectorGateway:
    """Route governed application requests to the Multi-Connector Adapter."""

    def __init__(self, adapter: MultiConnectorAdapter | None = None) -> None:
        self.adapter = adapter or MultiConnectorAdapter()

    @staticmethod
    def fingerprint_credential(credential: str) -> str:
        return MultiConnectorAdapter.fingerprint_credential(credential)

    def register(self, connector: Any, *, credential: str,
                 allowed_operations: set[str] | frozenset[str]) -> None:
        self.adapter.register(connector, credential=credential, allowed_operations=allowed_operations)

    def rotate_credential(self, connector_id: str, *, credential: str,
                          allowed_operations: set[str] | frozenset[str] | None = None) -> None:
        self.adapter.rotate_credential(connector_id, credential=credential, allowed_operations=allowed_operations)

    def revoke(self, connector_id: str) -> None:
        self.adapter.revoke(connector_id)

    def connector(self, connector_id: str) -> Any:
        return self.adapter.connector(connector_id)

    def authorize(self, connector_id: str, operation: str, *, credential: str, nonce: str) -> None:
        self.adapter.authorize(connector_id, operation, credential=credential, nonce=nonce)

    def dispatch(self, connector_id: str, operation: str, *, credential: str,
                 nonce: str, **kwargs: Any) -> Any:
        return self.adapter.dispatch(connector_id, operation, credential=credential, nonce=nonce, **kwargs)

    def audit_events(self) -> tuple[GatewayAuditEvent, ...]:
        return self.adapter.audit_events()

    def registered_connectors(self) -> tuple[str, ...]:
        return self.adapter.registered_connectors()


__all__ = ["GatewayAuditEvent", "OpenMultiConnectorGateway"]
