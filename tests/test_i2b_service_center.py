from architecture.contracts import ActorType, BoundaryRequest, BoundaryResponse
from services.i2b_service_center import I2BConnectionGateway, ServiceCenter


def test_service_center_dispatches_registered_service():
    center = ServiceCenter()
    center.register("asset-information", lambda request: {"asset_id": request.payload["asset_id"]})
    gateway = I2BConnectionGateway(service_center=center)

    response = gateway.handle(BoundaryRequest(
        actor_type=ActorType.COMPANY,
        actor_id="company-1",
        activity="asset-information",
        payload={"asset_id": "ASSET-1"},
        correlation_id="corr-1",
    ))

    assert response == BoundaryResponse(
        accepted=True,
        activity="asset-information",
        correlation_id="corr-1",
        data={"asset_id": "ASSET-1"},
    )


def test_unknown_activity_can_continue_to_connector():
    center = ServiceCenter()

    class Connector:
        def handle(self, request):
            return BoundaryResponse(True, request.activity, request.correlation_id, {"routed": True})

    gateway = I2BConnectionGateway(service_center=center, connector=Connector())
    response = gateway.handle(BoundaryRequest(ActorType.PERSON, "p-1", "person-action", correlation_id="c-1"))
    assert response.accepted is True
    assert response.data == {"routed": True}


def test_unknown_activity_fails_closed_without_connector():
    gateway = I2BConnectionGateway(service_center=ServiceCenter())
    response = gateway.handle(BoundaryRequest(ActorType.STATE, "s-1", "unknown"))
    assert response.accepted is False
