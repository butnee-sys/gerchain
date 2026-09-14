from architecture.contracts import ActorType, BoundaryRequest
from services.i2b_service_center import ServiceCenter
from services.i2b_services import register_core_services


class FakeGerchain:
    def get_balance(self, account_id):
        return 125

    def get_escrow_state(self):
        return {"escrow_id": "E1", "state": "LOCKED"}


def test_core_services_register_and_dispatch():
    center = ServiceCenter()
    register_core_services(center, gerchain=FakeGerchain())

    balance = center.dispatch(BoundaryRequest(
        ActorType.PERSON, "P1", "account-balance", {"account_id": "A1"}, correlation_id="C1"
    ))
    assert balance.accepted is True
    assert balance.data == {"account_id": "A1", "balance": 125}

    escrow = center.dispatch(BoundaryRequest(
        ActorType.COMPANY, "C1", "escrow-information", {}, correlation_id="C2"
    ))
    assert escrow.data["escrow"]["state"] == "LOCKED"


def test_asset_service_is_boundary_ready_without_nef():
    center = ServiceCenter()
    register_core_services(center)
    response = center.dispatch(BoundaryRequest(
        ActorType.STATE, "S1", "asset-information", {"asset_id": "ASSET-1"}
    ))
    assert response.accepted is True
    assert response.data["status"] == "SERVICE_BOUNDARY_READY"
