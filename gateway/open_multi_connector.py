"""Open Multi-Connector Gateway.

"Open" means extensible by registered connectors, not unauthenticated or
unrestricted. Connector identity is explicit so applications never receive
an implicit path to the EXIM Port.
"""

from typing import Any, Protocol


class ConnectorAdapter(Protocol):
    connector_id: str


class OpenMultiConnectorGateway:
    """Registry and controlled dispatch point for connector adapters."""

    def __init__(self) -> None:
        self._connectors: dict[str, ConnectorAdapter] = {}

    def register(self, adapter: ConnectorAdapter) -> None:
        connector_id = str(adapter.connector_id).strip()
        if not connector_id:
            raise ValueError("connector_id is required")
        if connector_id in self._connectors:
            raise ValueError(f"connector already registered: {connector_id}")
        self._connectors[connector_id] = adapter

    def revoke(self, connector_id: str) -> None:
        self._connectors.pop(connector_id, None)

    def connector(self, connector_id: str) -> ConnectorAdapter:
        try:
            return self._connectors[connector_id]
        except KeyError as exc:
            raise ValueError(f"connector is not registered: {connector_id}") from exc

    def dispatch(self, connector_id: str, operation: str, **kwargs: Any) -> Any:
        adapter = self.connector(connector_id)
        handler = getattr(adapter, operation, None)
        if handler is None or not callable(handler):
            raise ValueError(f"unsupported connector operation: {operation}")
        return handler(**kwargs)

    def registered_connectors(self) -> tuple[str, ...]:
        return tuple(sorted(self._connectors))


__all__ = ["OpenMultiConnectorGateway"]
