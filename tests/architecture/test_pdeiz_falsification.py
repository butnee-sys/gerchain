from __future__ import annotations

import base64

import pytest

from architecture.contracts import ActorType, BoundaryRequest
from services.g3_core_handler import G3CoreRuntimeHandler
from services.gerchain_runtime import GerchainRuntime
from dee_security.root_of_trust import RootOfTrust


def _handler() -> G3CoreRuntimeHandler:
    runtime = GerchainRuntime(
        escrow_id="pdeiz-escrow",
        amount=100,
        currency="MNT",
        witness_id="pdeiz-witness",
    )
    return G3CoreRuntimeHandler(runtime)


def _request(payload: dict) -> BoundaryRequest:
    return BoundaryRequest(
        actor_type=ActorType.COMPANY,
        actor_id="downstream-test-actor",
        activity="RELEASE",
        payload=payload,
        correlation_id="pdeiz-falsification",
    )


def _valid_preconditions() -> dict:
    return {
        "asset": {
            "asset_id": "asset-1",
            "validation_status": "VALID",
            "verification_id": "verify-1",
            "valuation_id": "value-1",
        },
        "condition_policy": {
            "trust": "PASS",
            "transparency": "PASS",
            "performance": "PASS",
        },
        "escrow": {"escrow_id": "pdeiz-escrow"},
        "decision": {"status": "APPROVE"},
        "authorization": {"status": "AUTHORIZED"},
        "_dee_context": {"root": RootOfTrust("owner-1", base64.b64encode(bytes(32)).decode("ascii")), "owner_id": "owner-1"},
        "destination": "beneficiary-1",
        "source": "pdeiz-escrow",
        "transaction_id": "tx-pdeiz-1",
        "timestamp": "2026-10-19T00:00:00Z",
    }


@pytest.mark.parametrize(
    ("field", "reason_fragment"),
    [
        ("authorization", "AUTHORIZED"),
        ("decision", "APPROVE"),
        ("_dee_context", "DEE authorization context"),
    ],
)
def test_release_fails_closed_when_authority_chain_is_incomplete(field, reason_fragment):
    payload = _valid_preconditions()
    payload.pop(field)

    response = _handler()(_request(payload))

    assert response.accepted is False
    assert response.reason is not None
    assert reason_fragment in response.reason


@pytest.mark.parametrize(
    ("condition", "expected_reason"),
    [
        ("trust", "G-3 escrow trinity is not PASS"),
        ("transparency", "G-3 escrow trinity is not PASS"),
        ("performance", "G-3 escrow trinity is not PASS"),
    ],
)
def test_release_fails_closed_when_any_trinity_condition_is_not_pass(condition, expected_reason):
    payload = _valid_preconditions()
    payload["condition_policy"][condition] = "UNKNOWN"

    response = _handler()(_request(payload))

    assert response.accepted is False
    assert response.reason == expected_reason


def test_downstream_payload_cannot_claim_nef_asset_truth_without_validation_evidence():
    payload = _valid_preconditions()
    payload["asset"]["validation_status"] = "UNVERIFIED"
    payload["asset"].pop("verification_id")

    response = _handler()(_request(payload))

    # The handler may pass governance gates, but the runtime release must still
    # be rejected because NEF asset evidence is not verified.
    assert response.accepted is False
