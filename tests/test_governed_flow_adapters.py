from architecture.contracts import ActorType, BoundaryRequest, BoundaryResponse
from architecture.governed_flow_adapters import (
    DEEToG3BoundaryAdapter,
    G3ToCoreBoundaryAdapter,
    CoreToEXIMBoundaryAdapter,
    EXIMToI2BBoundaryAdapter,
    I2BToEXIMBoundaryAdapter,
)


class Stub:
    def __init__(self, accepted=True):
        self.accepted = accepted

    def handle(self, request):
        return BoundaryResponse(
            accepted=self.accepted,
            activity=request.activity,
            correlation_id=request.correlation_id,
            data={"hop": True},
        )


def request():
    return BoundaryRequest(
        actor_type=ActorType.COMPANY,
        actor_id="company-1",
        activity="shuud-rapid-release",
        payload={},
        credential="cred",
        correlation_id="corr-1",
    )


def test_each_governed_boundary_requires_adapter_contract():
    downstream = Stub()
    chain = I2BToEXIMBoundaryAdapter(
        EXIMToI2BBoundaryAdapter(
            CoreToEXIMBoundaryAdapter(
                G3ToCoreBoundaryAdapter(
                    DEEToG3BoundaryAdapter(downstream)
                )
            )
        )
    )
    response = chain.handle(request())
    assert response.accepted is True
    assert response.correlation_id == "corr-1"


def test_adapter_fails_closed_on_invalid_downstream_response():
    class Invalid:
        def handle(self, request):
            return {"accepted": True}

    adapter = G3ToCoreBoundaryAdapter(Invalid())
    try:
        adapter.handle(request())
        assert False, "expected TypeError"
    except TypeError as exc:
        assert "BoundaryResponse" in str(exc)
