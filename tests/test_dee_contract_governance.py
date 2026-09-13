from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.contract_governance import (
    ContractGovernanceError,
    ProtectedContract,
    authorize_contract_change,
)
from dee_security.authorization import AuthorizationPolicy
from dee_security.root_of_trust import RootOfTrust, SignedChange


def _root() -> tuple[RootOfTrust, Ed25519PrivateKey]:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    return RootOfTrust("owner-1", base64.b64encode(public).decode()), private


def _change(private: Ed25519PrivateKey, owner: str = "owner-1") -> SignedChange:
    unsigned = SignedChange(owner, "change-1", 1, "contract-payload", "")
    payload = str(unsigned.signing_payload()).encode()
    signature = private.sign(payload)
    return SignedChange(
        owner,
        unsigned.change_id,
        unsigned.version,
        unsigned.payload_hash,
        base64.b64encode(signature).decode(),
    )


def test_contract_binds_to_root_owner_and_specification() -> None:
    root, _ = _root()
    spec = {"operation": "release", "limit": 2_000_000}
    contract = ProtectedContract.build(
        contract_id="shuud-release-v1",
        version=1,
        specification=spec,
        root=root,
    )
    assert contract.verify(root=root, specification=spec)
    assert not contract.verify(root=root, specification={"operation": "release"})


def test_contract_change_requires_root_authorization() -> None:
    root, private = _root()
    contract = ProtectedContract.build(
        contract_id="shuud-release-v1",
        version=1,
        specification={"operation": "release"},
        root=root,
    )
    authorize_contract_change(
        root=root,
        policy=AuthorizationPolicy(),
        change=_change(private),
        contract=contract,
        paths=("dee_security/contract_governance.py",),
    )


def test_wrong_contract_owner_fails_closed() -> None:
    root, _ = _root()
    contract = ProtectedContract(
        contract_id="foreign",
        version=1,
        contract_hash="x",
        owner_id="other-owner",
    )
    with pytest.raises(ContractGovernanceError):
        authorize_contract_change(
            root=root,
            policy=AuthorizationPolicy(),
            change=SignedChange("owner-1", "x", 1, "x", "x"),
            contract=contract,
            paths=("dee_security/contract_governance.py",),
        )
