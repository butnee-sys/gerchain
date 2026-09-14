from __future__ import annotations

from architecture.contracts import AdapterContract, BoundaryRequest, BoundaryResponse
from architecture.governed_flow_adapters import (
    DEToDEEBoundaryAdapter,
    DEEToG3BoundaryAdapter,
    G3ToCoreBoundaryAdapter,
    CoreToEXIMBoundaryAdapter,
    EXIMToI2BBoundaryAdapter,
)


class _LayerEndpoint(AdapterContract):
    """A layer endpoint whose only downstream path is its boundary adapter."""

    def __init__(self, downstream: AdapterContract) -> None:
        self._downstream = downstream

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        return self._downstream.handle(request)


class CanonicalComposition:
    """Single composition root for the frozen DE -> ... -> I2B topology.

    The root wires layer endpoints to their explicit boundary adapters. It
    never constructs or duplicates an operational engine.
    """

    def __init__(
        self,
        *,
        dee: AdapterContract,
        g3: AdapterContract,
        core: AdapterContract,
        exim: AdapterContract,
        i2b: AdapterContract,
    ) -> None:
        # Build the chain from the last boundary backwards. The supplied
        # endpoints represent the actual layer implementations; each layer
        # crosses its next boundary only through the corresponding adapter.
        exim_to_i2b = EXIMToI2BBoundaryAdapter(i2b)
        exim_endpoint = _LayerEndpoint(exim_to_i2b)
        core_to_exim = CoreToEXIMBoundaryAdapter(exim_endpoint)
        core_endpoint = _LayerEndpoint(core_to_exim)
        g3_to_core = G3ToCoreBoundaryAdapter(core_endpoint)
        g3_endpoint = _LayerEndpoint(g3_to_core)
        dee_to_g3 = DEEToG3BoundaryAdapter(g3_endpoint)
        dee_endpoint = _LayerEndpoint(dee_to_g3)

        self.de_to_dee = DEToDEEBoundaryAdapter(dee_endpoint)
        self.dee = dee
        self.g3 = g3
        self.core = core
        self.exim = exim
        self.i2b = i2b
        self.entry = self.de_to_dee

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        return self.entry.handle(request)


__all__ = ["CanonicalComposition"]
