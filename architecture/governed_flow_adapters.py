from __future__ import annotations

from architecture.contracts import AdapterContract, BoundaryRequest, BoundaryResponse
from architecture.ports import DEEToG3Adapter, G3ToCoreAdapter, CoreToEXIMAdapter, EXIMToI2BAdapter, I2BToEXIMAdapter


class GovernedBoundaryAdapter(AdapterContract):
    """Explicit adapter with fail-closed BoundaryRequest/BoundaryResponse contract."""

    def __init__(self, downstream: AdapterContract, name: str) -> None:
        self._downstream = downstream
        self.name = name

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        if not isinstance(request, BoundaryRequest):
            raise TypeError(f"{self.name} requires BoundaryRequest")
        response = self._downstream.handle(request)
        if not isinstance(response, BoundaryResponse):
            raise TypeError(f"{self.name} downstream must return BoundaryResponse")
        return response


class DEEToG3BoundaryAdapter(GovernedBoundaryAdapter, DEEToG3Adapter):
    def __init__(self, downstream: AdapterContract):
        super().__init__(downstream, "DEE_TO_G3")


class G3ToCoreBoundaryAdapter(GovernedBoundaryAdapter, G3ToCoreAdapter):
    def __init__(self, downstream: AdapterContract):
        super().__init__(downstream, "G3_TO_CORE")


class CoreToEXIMBoundaryAdapter(GovernedBoundaryAdapter, CoreToEXIMAdapter):
    def __init__(self, downstream: AdapterContract):
        super().__init__(downstream, "CORE_TO_EXIM")


class EXIMToI2BBoundaryAdapter(GovernedBoundaryAdapter, EXIMToI2BAdapter):
    def __init__(self, downstream: AdapterContract):
        super().__init__(downstream, "EXIM_TO_I2B")


class I2BToEXIMBoundaryAdapter(GovernedBoundaryAdapter, I2BToEXIMAdapter):
    def __init__(self, downstream: AdapterContract):
        super().__init__(downstream, "I2B_TO_EXIM")


__all__ = [
    "GovernedBoundaryAdapter",
    "DEEToG3BoundaryAdapter",
    "G3ToCoreBoundaryAdapter",
    "CoreToEXIMBoundaryAdapter",
    "EXIMToI2BBoundaryAdapter",
    "I2BToEXIMBoundaryAdapter",
]
