from __future__ import annotations

import base64
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.root_of_trust import RootOfTrust
from dee_security.witness_verification import WitnessVerificationError, WitnessVerificationProof, require_witness_verification


def _root() -> RootOfTrust:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    return RootOfTrust("owner-1", base64.b64encode(public).decode())


def _proof(**changes: object) -> WitnessVerificationProof:
    values = {
        "witness_verified": True,
        "independent_verifier_verified": True,
        "state_root_verified": True,
        "no_fork_verified": True,
    }
    values.update(changes)
    return WitnessVerificationProof(**values)


def test_complete_witness_verification_passes() -> None:
    require_witness_verification(
        root=_root(),
        owner_id="owner-1",
        proof=_proof(),
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )


@pytest.mark.parametrize("field", [
    "witness_verified",
    "independent_verifier_verified",
    "state_root_verified",
    "no_fork_verified",
])
def test_witness_verification_fails_closed(field: str) -> None:
    with pytest.raises(WitnessVerificationError):
        require_witness_verification(
            root=_root(),
            owner_id="owner-1",
            proof=_proof(**{field: False}),
            trinity_proof={"trust": True, "transparency": True, "performance": True},
        )


def test_witness_verification_requires_trinity() -> None:
    with pytest.raises(WitnessVerificationError):
        require_witness_verification(
            root=_root(),
            owner_id="owner-1",
            proof=_proof(),
            trinity_proof={"trust": True, "transparency": False, "performance": True},
        )
