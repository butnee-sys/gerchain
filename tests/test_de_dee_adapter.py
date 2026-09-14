from __future__ import annotations

import pytest

from architecture.contracts import ActorType, AdapterContract, BoundaryRequest, BoundaryResponse
from architecture.governed_flow_adapters import DEToDEEBoundaryAdapter


class RecordingDEE(AdapterContract):
    def __init__(self) -> None:
        self.requests: list[BoundaryRequest] = []

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        self.requests.append(request)
        return BoundaryResponse(
            accepted=True,
            activity=request.activity,
            correlation_id=request.correlation_id,
            data={"layer": "DEE"},
        )


class InvalidDEE(AdapterContract):
    def handle(self, request: BoundaryRequest):
        return {"accepted": True}


def test_de_to_dee_routes_only_through_boundary_contract() -> None:
    dee = RecordingDEE()
    adapter = DEToDEEBoundaryAdapter(dee)
    request = BoundaryRequest(
        actor_type=ActorType.COMPANY,
        actor_id="company-001",
        activity="digital-economic-activity",
        payload={"amount": 100},
        correlation_id="corr-001",
    )

    response = adapter.handle(request)

    assert response.accepted is True
    assert response.correlation_id == "corr-001"
    assert dee.requests == [request]


def test_de_to_dee_rejects_invalid_request() -> None:
    adapter = DEToDEEBoundaryAdapter(RecordingDEE())

    with pytest.raises(TypeError, match="DE_TO_DEE requires BoundaryRequest"):
        adapter.handle("not-a-boundary-request")  # type: ignore[arg-type]


def test_de_to_dee_fails_closed_on_invalid_downstream_response() -> None:
    adapter = DEToDEEBoundaryAdapter(InvalidDEE())
    request = BoundaryRequest(
        actor_type=ActorType.STATE,
        actor_id="state-001",
        activity="digital-economic-activity",
        correlation_id="corr-002",
    )

    with pytest.raises(TypeError, match="DE_TO_DEE downstream must return BoundaryResponse"):
        adapter.handle(request)
