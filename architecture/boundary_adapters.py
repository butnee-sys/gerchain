from __future__ import annotations

from typing import Any

from .contracts import AdapterContract, BoundaryRequest, BoundaryResponse


class ForwardingAdapter(AdapterContract):
    """Minimal boundary adapter: route only, never own business state."""

    def __init__(self, downstream: Any):
        self.downstream = downstream

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        response = self.downstream.handle(request)
        if not isinstance(response, BoundaryResponse):
            raise TypeError("adapter downstream must return BoundaryResponse")
        return response


class I2BToEXIMBoundaryAdapter(ForwardingAdapter):
    """I2B -> EXIM controlled crossing."""


class EXIMToI2BBoundaryAdapter(ForwardingAdapter):
    """EXIM -> I2B controlled crossing."""


class I2BServiceBoundaryAdapter(ForwardingAdapter):
    """I2B Connection Gateway -> Service Center crossing."""


__all__ = [
    "ForwardingAdapter",
    "I2BToEXIMBoundaryAdapter",
    "EXIMToI2BBoundaryAdapter",
    "I2BServiceBoundaryAdapter",
]
