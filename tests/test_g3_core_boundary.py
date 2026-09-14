from architecture.contracts import ActorType, BoundaryError, BoundaryRequest, BoundaryResponse
from architecture.g3_core import G3ToCoreBoundaryAdapter


def test_g3_core_adapter_forwards_nef_reference_and_policy_to_core():
    received = []

    def core_handler(request):
        received.append(request)
        return BoundaryResponse(
            accepted=True,
            activity=request.activity,
            correlation_id=request.correlation_id,
            data={"routed": True},
        )

    adapter = G3ToCoreBoundaryAdapter(core_handler)
    request = BoundaryRequest(
        actor_type=ActorType.COMPANY,
        actor_id="INSURER-001",
        activity="create_conditional_value_flow",
        correlation_id="CORR-001",
        payload={
            "asset": {
                "asset_id": "NEF-ASSET-001",
                "valuation_id": "VAL-001",
                "verification_id": "VER-001",
                "validation_status": "VALID",
                "asset_version": 1,
            },
            "condition_policy": {
                "trust": "PASS",
                "transparency": "PASS",
                "performance": "PENDING",
            },
            "escrow": {"amount": 2000000, "currency": "MNT"},
        },
    )

    response = adapter.handle(request)

    assert response.accepted is True
    assert len(received) == 1
    assert received[0].payload["asset"]["asset_id"] == "NEF-ASSET-001"
    assert received[0].payload["condition_policy"]["performance"] == "PENDING"
    assert received[0].payload["escrow"]["amount"] == 2000000


def test_g3_core_adapter_rejects_missing_asset_reference():
    adapter = G3ToCoreBoundaryAdapter(lambda request: BoundaryResponse(True, request.activity))
    request = BoundaryRequest(
        actor_type=ActorType.PERSON,
        actor_id="PERSON-001",
        activity="create_conditional_value_flow",
        payload={"condition_policy": {}, "escrow": {}},
    )

    try:
        adapter.handle(request)
    except BoundaryError as exc:
        assert "asset" in str(exc)
    else:
        raise AssertionError("missing NEF asset reference must fail closed")


def test_g3_core_adapter_rejects_missing_policy_or_escrow():
    adapter = G3ToCoreBoundaryAdapter(lambda request: BoundaryResponse(True, request.activity))
    base_asset = {"asset_id": "NEF-ASSET-002"}

    for payload in (
        {"asset": base_asset, "escrow": {}},
        {"asset": base_asset, "condition_policy": {}},
    ):
        try:
            adapter.handle(
                BoundaryRequest(
                    actor_type=ActorType.STATE,
                    actor_id="STATE-001",
                    activity="create_conditional_value_flow",
                    payload=payload,
                )
            )
        except BoundaryError:
            pass
        else:
            raise AssertionError("incomplete G-3/Core request must fail closed")


def test_g3_core_adapter_does_not_import_operational_engines():
    from pathlib import Path

    source = Path("architecture/g3_core.py").read_text(encoding="utf-8")
    forbidden = (
        "from escrow",
        "from money",
        "from witness",
        "from verifier",
        "from services",
        "from nef",
    )
    assert not any(token in source for token in forbidden)
