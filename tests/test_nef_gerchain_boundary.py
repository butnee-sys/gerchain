from architecture.contracts import ActorType, AdapterContract, BoundaryError, BoundaryRequest, BoundaryResponse
from architecture.nef_gerchain import NEFToGerChainAdapter


class CaptureAdapter(AdapterContract):
    def __init__(self):
        self.request = None

    def handle(self, request):
        self.request = request
        return BoundaryResponse(accepted=True, activity=request.activity, data={"routed": True})


def valid_asset():
    return {
        "asset_id": "NEF-ASSET-001",
        "valuation_id": "VAL-001",
        "verification_id": "VER-001",
        "validation_status": "VALID",
        "asset_version": 4,
        "value": 20_000_000,
        "currency": "MNT",
    }


def test_nef_reference_reaches_gerchain_boundary():
    downstream = CaptureAdapter()
    adapter = NEFToGerChainAdapter(downstream)
    response = adapter.handle(
        BoundaryRequest(
            actor_type=ActorType.COMPANY,
            actor_id="INSURER-001",
            activity="create_conditional_value_flow",
            correlation_id="CORR-NEF-001",
            payload={"asset": valid_asset(), "condition_policy": {}, "escrow": {2: 1}},
        )
    )

    assert response.accepted is True
    assert downstream.request is not None
    assert downstream.request.payload["asset"]["asset_id"] == "NEF-ASSET-001"
    assert downstream.request.payload["asset"]["value"] == 20_000_000
    assert downstream.request.payload["asset"]["validation_status"] == "VALID"


def test_nef_boundary_fails_closed_for_unverified_asset():
    downstream = CaptureAdapter()
    adapter = NEFToGerChainAdapter(downstream)
    asset = valid_asset()
    asset["validation_status"] = "INVALID"

    try:
        adapter.handle(
            BoundaryRequest(
                actor_type=ActorType.PERSON,
                actor_id="PERSON-001",
                activity="create_conditional_value_flow",
                payload={"asset": asset},
            )
        )
    except BoundaryError as exc:
        assert "VALID" in str(exc)
    else:
        raise AssertionError("invalid NEF asset must fail closed")


def test_nef_boundary_rejects_missing_valuation_reference():
    downstream = CaptureAdapter()
    adapter = NEFToGerChainAdapter(downstream)
    asset = valid_asset()
    del asset["valuation_id"]

    try:
        adapter.handle(
            BoundaryRequest(
                actor_type=ActorType.STATE,
                actor_id="STATE-001",
                activity="create_conditional_value_flow",
                payload={"asset": asset},
            )
        )
    except BoundaryError as exc:
        assert "valuation_id" in str(exc)
    else:
        raise AssertionError("missing valuation reference must fail closed")
