"""Boundary ports for Core -> EXIM -> I2B -> actor connectors.

Ports intentionally contain no operational value-flow logic. Implementations
must delegate to existing authoritative infrastructure through governed APIs.
"""

from __future__ import annotations

from .contracts import (
    ActorType,
    AdapterContract,
    BoundaryRequest,
    BoundaryResponse,
)


class CoreAdapter(AdapterContract):
    """Adapter between G-3/NEF+GerChain and the EXIM boundary."""


class EXIMPort(AdapterContract):
    """External-system boundary; core internals must not leak through it."""


class I2BGateway(AdapterContract):
    """Infrastructure-to-business boundary."""


class MultiConnectorAdapter(AdapterContract):
    """Routes governed business activity requests to one actor connector."""

    def __init__(self, connectors: dict[ActorType, AdapterContract]):
        self._connectors = dict(connectors)

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        connector = self._connectors.get(request.actor_type)
        if connector is None:
            return BoundaryResponse(
                accepted=False,
                activity=request.activity,
                correlation_id=request.correlation_id,
                reason=f"No connector registered for actor type: {request.actor_type.value}",
            )
        return connector.handle(request)


class StateConnector(AdapterContract):
    """State actor connector."""


class CompanyConnector(AdapterContract):
    """Company actor connector."""


class PersonConnector(AdapterContract):
    """Person actor connector."""


__all__ = [
    "CoreAdapter",
    "EXIMPort",
    "I2BGateway",
    "MultiConnectorAdapter",
    "StateConnector",
    "CompanyConnector",
    "PersonConnector",
]
