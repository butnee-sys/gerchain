"""Cross-connector isolation rules for the DEE I2B gateway."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .root_of_trust import RootOfTrust, SecurityError
from .trinity import TrinityError, require_trinity


class ConnectorIsolationError(SecurityError):
    """Raised when a connector attempts to cross its security boundary."""


@dataclass(frozen=True)
class ConnectorIsolationRequest:
    connector_id: str
    request_id: str
    actor_id: str
    nonce: str
    target_connector_id: str


def authorize_connector_isolation(
    *,
    root: RootOfTrust,
    request: ConnectorIsolationRequest,
    trinity_proof: Mapping[str, bool],
) -> None:
    """Fail closed if a connector targets another connector's security context."""
    for name, value in (
        ("connector_id", request.connector_id),
        ("request_id", request.request_id),
        ("actor_id", request.actor_id),
        ("nonce", request.nonce),
        ("target_connector_id", request.target_connector_id),
    ):
        if not str(value).strip():
            raise ConnectorIsolationError(f"{name} is required")
    if request.connector_id != request.target_connector_id:
        raise ConnectorIsolationError("cross-connector access is denied")
    if request.actor_id != root.owner_id:
        raise ConnectorIsolationError("connector actor is not bound to DEE Owner")
    try:
        require_trinity(trinity_proof)
    except TrinityError as exc:
        raise ConnectorIsolationError(str(exc)) from exc


__all__ = ["ConnectorIsolationError", "ConnectorIsolationRequest", "authorize_connector_isolation"]
