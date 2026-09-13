"""Open Multi-Connector Gateway with explicit connector trust controls.

"Open" means extensible by registered connectors, not unauthenticated or
unrestricted. Every connector is authenticated at registration and every
protected dispatch requires the connector credential plus a fresh nonce.
Credentials are stored only as fingerprints; audit records never contain
credential material.
"""

from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
from typing import Any, Protocol


class ConnectorAdapter(Protocol):
    connector_id: str


@dataclass(frozen=True)
class ConnectorCredential:
    connector_id: str
    credential_fingerprint: str
    allowed_operations: frozenset[str]
    active: bool = True


@dataclass(frozen=True)
class GatewayAuditEvent:
    event: str
    connector_id: str
    operation: str | None = None
    outcome: str = "SUCCESS"


class OpenMultiConnectorGateway:
    """Registry and controlled dispatch point for connector adapters."""

    def __init__(self) -> None:
        self._connectors: dict[str, ConnectorAdapter] = {}
        self._credentials: dict[str, ConnectorCredential] = {}
        self._used_nonces: set[tuple[str, str]] = set()
        self._audit: list[GatewayAuditEvent] = []

    @staticmethod
    def fingerprint_credential(credential: str) -> str:
        value = str(credential).strip()
        if not value:
            raise ValueError("credential is required")
        return sha256(value.encode("utf-8")).hexdigest()

    def _record(self, event: str, connector_id: str, operation: str | None = None,
                outcome: str = "SUCCESS") -> None:
        self._audit.append(GatewayAuditEvent(event, connector_id, operation, outcome))

    def register(
        self,
        adapter: ConnectorAdapter,
        *,
        credential: str,
        allowed_operations: set[str] | frozenset[str],
    ) -> None:
        connector_id = str(adapter.connector_id).strip()
        if not connector_id:
            raise ValueError("connector_id is required")
        if connector_id in self._connectors:
            raise ValueError(f"connector already registered: {connector_id}")
        operations = frozenset(str(value).strip() for value in allowed_operations)
        if not operations:
            raise ValueError("allowed_operations are required")
        credential_record = ConnectorCredential(
            connector_id=connector_id,
            credential_fingerprint=self.fingerprint_credential(credential),
            allowed_operations=operations,
        )
        self._connectors[connector_id] = adapter
        self._credentials[connector_id] = credential_record
        self._record("REGISTER", connector_id)

    def rotate_credential(
        self,
        connector_id: str,
        *,
        credential: str,
        allowed_operations: set[str] | frozenset[str] | None = None,
    ) -> None:
        if connector_id not in self._connectors:
            raise ValueError(f"connector is not registered: {connector_id}")
        current = self._credentials.get(connector_id)
        if current is None:
            raise ValueError(f"connector credentials are not registered: {connector_id}")
        operations = frozenset(str(value).strip() for value in (allowed_operations or current.allowed_operations))
        if not operations:
            raise ValueError("allowed_operations are required")
        self._credentials[connector_id] = ConnectorCredential(
            connector_id=connector_id,
            credential_fingerprint=self.fingerprint_credential(credential),
            allowed_operations=operations,
            active=True,
        )
        self._record("ROTATE_CREDENTIAL", connector_id)

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
        self._record("REVOKE", connector_id)

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
        if not compare_digest(self.fingerprint_credential(credential), registered.credential_fingerprint):
            self._record("AUTHORIZE", connector_id, operation, "DENIED")
            raise ValueError(f"connector authentication failed: {connector_id}")
        if operation not in registered.allowed_operations:
            self._record("AUTHORIZE", connector_id, operation, "DENIED")
            raise ValueError(f"connector operation is not authorized: {operation}")
        nonce_key = (connector_id, str(nonce).strip())
        if nonce_key in self._used_nonces:
            self._record("AUTHORIZE", connector_id, operation, "REPLAY_DENIED")
            raise ValueError(f"request nonce already used: {nonce}")
        self._used_nonces.add(nonce_key)
        self._record("AUTHORIZE", connector_id, operation)

    def dispatch(
        self,
        connector_id: str,
        operation: str,
        *,
        credential: str,
        nonce: str,
        **kwargs: Any,
    ) -> Any:
        self.connector(connector_id)
        self.authorize(connector_id, operation, credential=credential, nonce=nonce)
        adapter = self.connector(connector_id)
        handler = getattr(adapter, operation, None)
        if handler is None or not callable(handler):
            self._record("DISPATCH", connector_id, operation, "DENIED")
            raise ValueError(f"unsupported connector operation: {operation}")
        result = handler(**kwargs)
        self._record("DISPATCH", connector_id, operation)
        return result

    def audit_events(self) -> tuple[GatewayAuditEvent, ...]:
        return tuple(self._audit)

    def registered_connectors(self) -> tuple[str, ...]:
        return tuple(sorted(self._connectors))


__all__ = ["ConnectorCredential", "GatewayAuditEvent", "OpenMultiConnectorGateway"]
