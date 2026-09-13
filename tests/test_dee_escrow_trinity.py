from __future__ import annotations

import base64
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.escrow_trinity import EscrowExecutionProof, EscrowTrinityError, require_escrow_trinity
from dee_security.root_of_trust import RootOfTrust


def _root() -> RootOfTrust:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    return RootOfTrust("owner-1", base64.b64encode(public).decode())


def _proof(**changes: object) -> EscrowExecutionProof:
    values = {
        "escrow_id": "ESC-1",
        "transition_id": "TX-1",
        "authorized": True,
        "evidence_verified": True,
        "witness_ready": True,
    }
    values.update(changes)
    return EscrowExecutionProof(**values)


def test_escrow_execution_requires_complete_trinity() -> None:
    require_escrow_trinity(
        root=_root(),
        owner_id="owner-1",
        proof=_proof(),
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )


@pytest.mark.parametrize("field", ["authorized", "evidence_verified", "witness_ready"])
def test_escrow_execution_fails_closed_without_required_proof(field: str) -> None:
    with pytest.raises(EscrowTrinityError):
        require_escrow_trinity(
            root=_root(),
            owner_id="owner-1",
            proof=_proof(**{field: False}),
            trinity_proof={"trust": True, "transparency": True, "performance": True},
        )


def test_escrow_execution_rejects_incomplete_trinity() -> None:
    with pytest.raises(EscrowTrinityError):
        require_escrow_trinity(
            root=_root(),
            owner_id="owner-1",
            proof=_proof(),
            trinity_proof={"trust": True, "transparency": True},
        )
