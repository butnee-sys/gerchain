from architecture.contracts import ActorType, BoundaryRequest, BoundaryResponse
from services.exim_gateway import EXIMGateway
from services.i2b_service_center import ServiceCenter
from apps.shuud.integration.shuud_exim_flow import SHUUDEximFlow
from apps.shuud.service import SHUUDService


def make_request(**payload):
    return BoundaryRequest(ActorType.PERSON, "driver-1", "shuud-rapid-release", payload, correlation_id="C-E2E")


def test_shuud_reaches_exim_only_after_service_validation():
    center = ServiceCenter()
    center.register("shuud-rapid-release", SHUUDService().handle)
    seen = []

    class Downstream:
        def handle(self, request):
            seen.append(request.activity)
            return BoundaryResponse(True, request.activity, request.correlation_id, {"core": "accepted"})

    response = SHUUDEximFlow(exim=EXIMGateway(Downstream()), service_center=center).handle(make_request(incident_id="I-1", vehicle_id="V-1", compensation=1_000_000, evidence_verified=True))
    assert response.accepted is True
    assert seen == ["shuud-rapid-release"]


def test_invalid_shuud_request_never_reaches_exim():
    center = ServiceCenter()
    center.register("shuud-rapid-release", SHUUDService().handle)
    seen = []

    class Downstream:
        def handle(self, request):
            seen.append(request.activity)
            return BoundaryResponse(True, request.activity, request.correlation_id)

    response = SHUUDEximFlow(exim=EXIMGateway(Downstream()), service_center=center).handle(make_request(incident_id="I-2", vehicle_id="V-2", compensation=1_000_000, evidence_verified=False))
    assert response.accepted is False
    assert seen == []
