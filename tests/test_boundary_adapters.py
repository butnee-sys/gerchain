from architecture.boundary_adapters import I2BToEXIMBoundaryAdapter
from architecture.contracts import ActorType, BoundaryRequest, BoundaryResponse


class Target:
    def handle(self, request):
        return BoundaryResponse(True, request.activity, request.correlation_id, {"crossed": True})


def test_i2b_to_exim_crossing_uses_adapter():
    adapter = I2BToEXIMBoundaryAdapter(Target())
    response = adapter.handle(BoundaryRequest(
        ActorType.PERSON, "P1", "shuud-rapid-release", {}, correlation_id="C1"
    ))
    assert response.accepted is True
    assert response.data == {"crossed": True}
