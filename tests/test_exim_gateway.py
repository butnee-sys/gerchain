from architecture.contracts import ActorType, BoundaryRequest, BoundaryResponse
from services.exim_gateway import EXIMGateway


class Downstream:
    def handle(self, request):
        return BoundaryResponse(True, request.activity, request.correlation_id, {"routed": True})


def test_exim_routes_only_valid_boundary_request():
    gateway = EXIMGateway(Downstream())
    response = gateway.handle(BoundaryRequest(
        ActorType.COMPANY, "company-1", "shuud-rapid-release", {}, correlation_id="C-1"
    ))
    assert response.accepted is True
    assert response.data == {"routed": True}


def test_exim_rejects_missing_correlation_id():
    response = EXIMGateway(Downstream()).handle(
        BoundaryRequest(ActorType.PERSON, "person-1", "shuud-rapid-release")
    )
    assert response.accepted is False


def test_exim_fails_closed_when_not_configured():
    response = EXIMGateway().handle(
        BoundaryRequest(ActorType.PERSON, "person-1", "shuud-rapid-release", correlation_id="C-2")
    )
    assert response.accepted is False
