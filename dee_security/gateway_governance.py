"""DEE governance gate for the I2B Multi-Connector Gateway."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .connector_governance import ConnectorAccessRequest, authorize_connector_access
from .root_of_trust import RootOfTrust, SecurityError
from .trinity import TrinityError, require_trinity


class GatewayGovernanceError(SecurityError):
    """Raised when a gateway operation is not governed by DEE."""


@dataclass(frozen=True)
class GatewayAccessRequest:
    gateway_id: str
    connector_id: str
    operation: str
    request_id: str
    actor_id: str
    nonce: str


def authorize_gateway_access(
    *,
    root: RootOfTrust,
    request: GatewayAccessRequest,
    trinity_proof: Mapping[str, bool],
) -> None:
    """Authorize gateway entry without granting the gateway independent authority."""
    for name, value in (
        ("gateway_id", request.gateway_id),
        ("connector_id", request.connector_id),
        ("operation", request.operation),
        ("request_id", request.request_id),
        ("actor_id", request.actor_id),
        ("nonce", request.nonce),
    ):
        if not str(value).strip():
            raise GatewayGovernanceError(f"{name} is required")
    try:
        require_trinity(trinity_proof)
        authorize_connector_access(
            root=root,
            request=ConnectorAccessRequest(
                connector_id=request.connector_id,
                operation=request.operation,
                request_id=request.request_id,
                actor_id=request.actor_id,
                nonce=request.nonce,
            ),
            trinity_proof=trinity_proof,
        )
    except (SecurityError, TrinityError) as exc:
        raise GatewayGovernanceError(str(exc)) from exc


__all__ = ["GatewayAccessRequest", "GatewayGovernanceError", "authorize_gateway_access"]
