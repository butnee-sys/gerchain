from __future__ import annotations

from architecture.composition_root import CanonicalComposition
from architecture.contracts import ActorType, AdapterContract, BoundaryRequest, BoundaryResponse


class Layer(AdapterContract):
    def __init__(self, name: str, trace: list[str], *, accept: bool = True) -> None:
        self.name = name
        self.trace = trace
        self.accept = accept

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        self.trace.append(self.name)
        return BoundaryResponse(
            accepted=self.accept,
            activity=request.activity,
            correlation_id=request.correlation_id,
            data={"layer": self.name},
            reason=None if self.accept else f"{self.name} denied",
        )


def request() -> BoundaryRequest:
    return BoundaryRequest(
        actor_type=ActorType.COMPANY,
        actor_id="company-001",
        activity="digital-economic-activity",
        correlation_id="corr-composition-001",
    )


def test_canonical_composition_crosses_all_layers_in_order() -> None:
    trace: list[str] = []
    composition = CanonicalComposition(
        dee=Layer("DEE", trace),
        g3=Layer("G3", trace),
        core=Layer("CORE", trace),
        exim=Layer("EXIM", trace),
        i2b=Layer("I2B", trace),
    )

    response = composition.handle(request())

    assert response.accepted is True
    assert trace == ["DEE", "G3", "CORE", "EXIM", "I2B"]


def test_canonical_composition_stops_on_layer_rejection() -> None:
    trace: list[str] = []
    composition = CanonicalComposition(
        dee=Layer("DEE", trace),
        g3=Layer("G3", trace, accept=False),
        core=Layer("CORE", trace),
        exim=Layer("EXIM", trace),
        i2b=Layer("I2B", trace),
    )

    response = composition.handle(request())

    assert response.accepted is False
    assert trace == ["DEE", "G3"]
