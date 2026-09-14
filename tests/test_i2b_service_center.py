from architecture.contracts import ActorType, BoundaryRequest, BoundaryResponse
from services.i2b_service_center import I2BConnectionGateway, ServiceCenter


def test_service_center_dispatches_registered_service():
    center = ServiceCenter()
    center.register("asset-information", lambda request: {"asset_id": request.payload["asset_id"]})
    gateway = I2BConnectionGateway(service_center=center)
    response = gateway.handle(BoundaryRequest(ActorType.COMPANY, "company-1", "asset-information", {"asset_id": "ASSET-1"}, correlation_id="corr-1"))
    assert response == BoundaryResponse(True, "asset-information", "corr-1", {"asset_id": "ASSET-1"})


def test_unknown_activity_routes_by_actor_type_to_multi_connector():
    class Connector:
        def __init__(self, name): self.name = name
        def handle(self, request): return BoundaryResponse(True, request.activity, request.correlation_id, {"connector": self.name})

    gateway = I2BConnectionGateway(
        service_center=ServiceCenter(),
        connectors={ActorType.STATE: Connector("state"), ActorType.COMPANY: Connector("company"), ActorType.PERSON: Connector("person")},
    )
    for actor_type, expected in ((ActorType.STATE, "state"), (ActorType.COMPANY, "company"), (ActorType.PERSON, "person")):
        response = gateway.handle(BoundaryRequest(actor_type, "actor-1", "actor-action", correlation_id="c-1"))
        assert response.accepted is True
        assert response.data == {"connector": expected}


def test_unknown_actor_type_fails_closed_with_multi_connector():
    class Connector:
        def handle(self, request): return BoundaryResponse(True, request.activity, request.correlation_id)
    gateway = I2BConnectionGateway(service_center=ServiceCenter(), connectors={ActorType.STATE: Connector()})
    response = gateway.handle(BoundaryRequest(ActorType.PERSON, "p-1", "person-action"))
    assert response.accepted is False


def test_legacy_single_connector_still_works():
    class Connector:
        def handle(self, request): return BoundaryResponse(True, request.activity, request.correlation_id, {"routed": True})
    gateway = I2BConnectionGateway(service_center=ServiceCenter(), connector=Connector())
    response = gateway.handle(BoundaryRequest(ActorType.PERSON, "p-1", "person-action", correlation_id="c-1"))
    assert response.accepted is True
    assert response.data == {"routed": True}


def test_unknown_activity_fails_closed_without_connector():
    gateway = I2BConnectionGateway(service_center=ServiceCenter())
    response = gateway.handle(BoundaryRequest(ActorType.STATE, "s-1", "unknown"))
    assert response.accepted is False
