from __future__ import annotations

from architecture.contracts import AdapterContract, BoundaryRequest, BoundaryResponse
from architecture.governed_flow_adapters import (
    DEToDEEBoundaryAdapter,
    DEEToG3BoundaryAdapter,
    G3ToCoreBoundaryAdapter as GovernedG3ToCoreBoundaryAdapter,
    CoreToEXIMBoundaryAdapter,
    EXIMToI2BBoundaryAdapter,
    I2BToEXIMBoundaryAdapter,
)
from architecture.ports import I2BToMultiConnectorAdapter


class _Endpoint(AdapterContract):
    """Small composition endpoint used only to terminate a boundary chain."""

    def __init__(self, handler):
        self._handler = handler

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        response = self._handler(request)
        if not isinstance(response, BoundaryResponse):
            raise TypeError("composition endpoint must return BoundaryResponse")
        return response


class CanonicalComposition:
    """Single composition root for the frozen DE -> ... -> I2B topology.

    This object wires boundaries only. It does not create ledger, escrow,
    witness, authorization, release, settlement, or asset-truth engines.
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
        i2b_adapter = EXIMToI2BBoundaryAdapter(i2b)
        core_to_exim = CoreToEXIMBoundaryAdapter(exim)
        g3_to_core = GovernedG3ToCoreBoundaryAdapter(core)
        dee_to_g3 = DEEToG3BoundaryAdapter(g3)

        self.de_to_dee = DEToDEEBoundaryAdapter(dee)
        self.dee_to_g3 = dee_to_g3
        self.g3_to_core = g3_to_core
        self.core_to_exim = core_to_exim
        self.exim_to_i2b = i2b_adapter

        # The public entry point is deliberately the first adapter, not a
        # layer implementation. Each layer is therefore reachable only via
        # its explicit boundary adapter.
        self.entry = self.de_to_dee

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        return self.entry.handle(request)


__all__ = ["CanonicalComposition"]
