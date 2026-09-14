from __future__ import annotations

from architecture.contracts import AdapterContract, BoundaryRequest, BoundaryResponse
from architecture.ports import DEAdapter


class DEToDEEAdapter(DEAdapter):
    """Concrete DE -> DEE boundary adapter.

    DE remains the top-level economic layer; DEE receives only a governed
    BoundaryRequest. No DEE/core state or engine is exposed here.
    """

    def __init__(self, downstream: AdapterContract) -> None:
        self._downstream = downstream

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        if not isinstance(request, BoundaryRequest):
            raise TypeError("DE_TO_DEE requires BoundaryRequest")
        response = self._downstream.handle(request)
        if not isinstance(response, BoundaryResponse):
            raise TypeError("DE_TO_DEE downstream must return BoundaryResponse")
        return response


__all__ = ["DEToDEEAdapter"]
