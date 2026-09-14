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
    """Run one layer endpoint, then cross its explicit downstream adapter."""

    def __init__(self, layer: AdapterContract, downstream: AdapterContract) -> None:
        self._layer = layer
        self._downstream = downstream

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        response = self._layer.handle(request)
        if not isinstance(response, BoundaryResponse):
            raise TypeError("layer endpoint must return BoundaryResponse")
        if not response.accepted:
            return response
        return self._downstream.handle(request)


class CanonicalComposition:
    """Single composition root for the frozen DE -> ... -> I2B topology."""

    def __init__(
        self,
        *,
        dee: AdapterContract,
        g3: AdapterContract,
        core: AdapterContract,
        exim: AdapterContract,
        i2b: AdapterContract,
    ) -> None:
        # Build from the destination backwards. Every hop is explicitly
        # Layer -> Adapter -> Layer and a rejected layer response stops flow.
        exim_to_i2b = EXIMToI2BBoundaryAdapter(i2b)
        exim_endpoint = _LayerEndpoint(exim, exim_to_i2b)
        core_to_exim = CoreToEXIMBoundaryAdapter(exim_endpoint)
        core_endpoint = _LayerEndpoint(core, core_to_exim)
        g3_to_core = G3ToCoreBoundaryAdapter(core_endpoint)
        g3_endpoint = _LayerEndpoint(g3, g3_to_core)
        dee_to_g3 = DEEToG3BoundaryAdapter(g3_endpoint)
        dee_endpoint = _LayerEndpoint(dee, dee_to_g3)

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
