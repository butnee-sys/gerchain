"""Open Multi-Connector Gateway with explicit connector trust controls.

"Open" means extensible by registered connectors, not unauthenticated or
unrestricted. Every dispatch must present an active connector identity,
operation authorization, and a request nonce that has not already been used.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Protocol


class ConnectorAdapter(Protocol):
    connector_id: str


@dataclass(frozen=True)
class ConnectorCredential:
    connector_id: str
    credential_fingerprint: str
    allowed_operations: frozenset[str]
    active: bool = True


class OpenMultiConnectorGateway:
    """Registry and controlled dispatch point for connector adapters."""

    def __init__(self) -> None:
        self._connectors: dict[str, ConnectorAdapter] = {}
        self._credentials: dict[str, ConnectorCredential] = {}
        self._used_nonces: set[tuple[str, str]] = set()

    @staticmethod
    def fingerprint_credential(credential: str) -> str:
        value = str(credential).strip()
        if not value:
            raise ValueError("credential is required")
        return sha256(value.encode("utf-8")).hexdigest()

    def register(
        self,
        adapter: ConnectorAdapter,
        *,
        credential: str | None = None,
        allowed_operations: set[str] | frozenset[str] | None = None,
    ) -> None:
        connector_id = str(adapter.connector_id).strip()
        if not connector_id:
            raise ValueError("connector_id is required")
        if connector_id in self._connectors:
            raise ValueError(f"connector already registered: {connector_id}")
        self._connectors[connector_id] = adapter
        if credential is not None:
            operations = frozenset(str(value).strip() for value in (allowed_operations or set()))
            if not operations:
                raise ValueError("allowed_operations are required for authenticated connectors")
            self._credentials[connector_id] = ConnectorCredential(
                connector_id=connector_id,
                credential_fingerprint=self.fingerprint_credential(credential),
                allowed_operations=operations,
            )

    def revoke(self, connector_id: str) -> None:
        self._connectors.pop(connector_id, None)
        credential = self._credentials.get(connector_id)
        if credential is not None:
            self._credentials[connector_id] = ConnectorCredential(
                connector_id=credential.connector_id,
                credential_fingerprint=credential.credential_fingerprint,
                allowed_operations=credential.allowed_operations,
                active=False,
            )

    def connector(self, connector_id: str) -> ConnectorAdapter:
        try:
            return self._connectors[connector_id]
        except KeyError as exc:
            raise ValueError(f"connector is not registered: {connector_id}") from exc

    def authorize(
        self,
        connector_id: str,
        operation: str,
        *,
        credential: str,
        nonce: str,
    ) -> None:
        if not str(nonce).strip():
            raise ValueError("request nonce is required")
        registered = self._credentials.get(connector_id)
        if registered is None:
            raise ValueError(f"connector credentials are not registered: {connector_id}")
        if not registered.active:
            raise ValueError(f"connector is revoked: {connector_id}")
        if self.fingerprint_credential(credential) != registered.credential_fingerprint:
            raise ValueError(f"connector authentication failed: {connector_id}")
        if operation not in registered.allowed_operations:
            raise ValueError(f"connector operation is not authorized: {operation}")
        nonce_key = (connector_id, str(nonce).strip())
        if nonce_key in self._used_nonces:
            raise ValueError(f"request nonce already used: {nonce}")
        self._used_nonces.add(nonce_key)

    def dispatch(
        self,
        connector_id: str,
        operation: str,
        *,
        credential: str | None = None,
        nonce: str | None = None,
        **kwargs: Any,
    ) -> Any:
        self.connector(connector_id)
        if credential is not None or nonce is not None:
            if credential is None or nonce is None:
                raise ValueError("credential and nonce are required together")
            self.authorize(connector_id, operation, credential=credential, nonce=nonce)
        elif connector_id in self._credentials:
            raise ValueError("authenticated connector requires credential and nonce")
        adapter = self.connector(connector_id)
        handler = getattr(adapter, operation, None)
        if handler is None or not callable(handler):
            raise ValueError(f"unsupported connector operation: {operation}")
        return handler(**kwargs)

    def registered_connectors(self) -> tuple[str, ...]:
        return tuple(sorted(self._connectors))


__all__ = ["ConnectorCredential", "OpenMultiConnectorGateway"]
