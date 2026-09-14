"""Explicit adapters and ports for the frozen DE architecture.

Adapters contain boundary routing only. They do not implement or duplicate
ledger, escrow, release, settlement, witness, or authoritative asset truth.
"""

from __future__ import annotations

from .contracts import ActorType, AdapterContract, BoundaryRequest, BoundaryResponse


class DEAdapter(AdapterContract):
    """Top-level DE boundary adapter into the DEE ecosystem."""


class DEEToG3Adapter(AdapterContract):
    """Adapter between DEE governance/protection and G-3 policy foundation."""


class G3ToCoreAdapter(AdapterContract):
    """Adapter between G-3 rules and NEF + GerChain core infrastructure."""


class CoreAdapter(G3ToCoreAdapter):
    """Compatibility name for the G-3/core boundary adapter."""


class CoreToEXIMAdapter(AdapterContract):
    """Adapter from authoritative core infrastructure to EXIM Port."""


class EXIMPort(AdapterContract):
    """External-system boundary; core internals must not leak through it."""


class EXIMToI2BAdapter(AdapterContract):
    """Adapter from EXIM Port into the I2B business boundary."""


class I2BGateway(AdapterContract):
    """Infrastructure-to-business boundary."""


class I2BToMultiConnectorAdapter(AdapterContract):
    """Adapter from I2B to the actor connector boundary."""


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
    "DEAdapter",
    "DEEToG3Adapter",
    "G3ToCoreAdapter",
    "CoreAdapter",
    "CoreToEXIMAdapter",
    "EXIMPort",
    "EXIMToI2BAdapter",
    "I2BGateway",
    "I2BToMultiConnectorAdapter",
    "MultiConnectorAdapter",
    "StateConnector",
    "CompanyConnector",
    "PersonConnector",
]
