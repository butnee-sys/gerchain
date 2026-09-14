from __future__ import annotations

from architecture.contracts import AdapterContract, BoundaryRequest, BoundaryResponse
from architecture.governed_flow_adapters import (
    DEToDEEBoundaryAdapter,
    DEEToG3BoundaryAdapter,
    G3ToCoreBoundaryAdapter,
    CoreToEXIMBoundaryAdapter,
    EXIMToI2BBoundaryAdapter,
)


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
        # Compose backwards from the destination so every layer is reached
        # through exactly one explicit adapter.
        self.exim_to_i2b = EXIMToI2BBoundaryAdapter(i2b)
        self.core_to_exim = CoreToEXIMBoundaryAdapter(self.exim_to_i2b)
        self.g3_to_core = G3ToCoreBoundaryAdapter(self.core_to_exim)
        self.dee_to_g3 = DEEToG3BoundaryAdapter(self.g3_to_core)
        self.de_to_dee = DEToDEEBoundaryAdapter(self.dee_to_g3)

        # Retain injected endpoints for inspection/testing. They are not
        # called directly by the public entry point.
        self.dee = dee
        self.g3 = g3
        self.core = core
        self.exim = exim
        self.i2b = i2b
        self.entry = self.de_to_dee

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        return self.entry.handle(request)


__all__ = ["CanonicalComposition"]
