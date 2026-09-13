"""DEE governance gate for connector-to-EXIM operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .core_access import CoreAccessRequest, authorize_core_access
from .root_of_trust import RootOfTrust, SecurityError
from .trinity import TrinityError, require_trinity


class ConnectorGovernanceError(SecurityError):
    """Raised when a connector cannot enter the protected infrastructure."""


@dataclass(frozen=True)
class ConnectorAccessRequest:
    connector_id: str
    operation: str
    request_id: str
    actor_id: str
    nonce: str


def authorize_connector_access(
    *,
    root: RootOfTrust,
    request: ConnectorAccessRequest,
    trinity_proof: Mapping[str, bool],
) -> None:
    """Fail-closed connector gate; adapters never become authority."""
    for name, value in (
        ("connector_id", request.connector_id),
        ("operation", request.operation),
        ("request_id", request.request_id),
        ("actor_id", request.actor_id),
        ("nonce", request.nonce),
    ):
        if not str(value).strip():
            raise ConnectorGovernanceError(f"{name} is required")

    try:
        require_trinity(trinity_proof)
        authorize_core_access(
            root=root,
            request=CoreAccessRequest(
                actor_id=request.actor_id,
                operation=request.operation,
                entrypoint="CORE_ADAPTER",
                request_id=request.request_id,
            ),
            authorized_actor_id=root.owner_id,
            trinity_proof=trinity_proof,
        )
    except SecurityError as exc:
        raise ConnectorGovernanceError(str(exc)) from exc
    except TrinityError as exc:
        raise ConnectorGovernanceError(str(exc)) from exc


__all__ = ["ConnectorAccessRequest", "ConnectorGovernanceError", "authorize_connector_access"]
