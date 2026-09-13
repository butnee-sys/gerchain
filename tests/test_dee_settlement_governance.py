from dee_security.settlement_governance import (
    SettlementAuthorization,
    SettlementGovernanceError,
    authorize_settlement,
)


def _root():
    from dee_security.root_of_trust import RootOfTrust
    return RootOfTrust(owner_id="owner-1", genesis_hash="genesis-1", policy_version=1)


def _authorization(**overrides):
    values = {
        "transaction_id": "tx-1",
        "escrow_id": "escrow-1",
        "owner_id": "owner-1",
        "authorized": True,
        "evidence_verified": True,
    }
    values.update(overrides)
    return SettlementAuthorization(**values)


def test_valid_settlement_is_authorized():
    authorize_settlement(
        root=_root(),
        authorization=_authorization(),
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )


def test_settlement_requires_owner_binding():
    try:
        authorize_settlement(
            root=_root(),
            authorization=_authorization(owner_id="other"),
            trinity_proof={"trust": True, "transparency": True, "performance": True},
        )
    except SettlementGovernanceError:
        return
    raise AssertionError("owner binding must fail closed")


def test_settlement_requires_trinity():
    try:
        authorize_settlement(
            root=_root(),
            authorization=_authorization(),
            trinity_proof={"trust": True, "transparency": False, "performance": True},
        )
    except SettlementGovernanceError:
        return
    raise AssertionError("incomplete Trinity must fail closed")
