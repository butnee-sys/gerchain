"""DEE-governed Witness Chain and Independent Verification gate."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .root_of_trust import RootOfTrust, SecurityError
from .trinity import TrinityError, require_trinity


class WitnessVerificationError(SecurityError):
    """Raised when witness/verification proof is insufficient."""


@dataclass(frozen=True)
class WitnessVerificationProof:
    witness_verified: bool
    independent_verifier_verified: bool
    state_root_verified: bool
    no_fork_verified: bool


def require_witness_verification(
    *,
    root: RootOfTrust,
    owner_id: str,
    proof: WitnessVerificationProof,
    trinity_proof: Mapping[str, bool],
) -> None:
    """Fail-closed transparency gate for protected execution."""
    if owner_id != root.owner_id:
        raise WitnessVerificationError("witness verification is not bound to DEE Root of Trust")
    if not proof.witness_verified:
        raise WitnessVerificationError("witness chain verification is required")
    if not proof.independent_verifier_verified:
        raise WitnessVerificationError("independent verification is required")
    if not proof.state_root_verified:
        raise WitnessVerificationError("state root verification is required")
    if not proof.no_fork_verified:
        raise WitnessVerificationError("no-fork verification is required")
    try:
        require_trinity(trinity_proof)
    except TrinityError as exc:
        raise WitnessVerificationError(str(exc)) from exc


def verify_witness_bundle(verifier: Any, bundle: Mapping[str, Any]) -> bool:
    """Run the existing independent verifier without trusting stored hashes."""
    if not isinstance(bundle, Mapping):
        return False
    try:
        return bool(verifier.verify_bundle(dict(bundle)))
    except (TypeError, ValueError, KeyError):
        return False


__all__ = [
    "WitnessVerificationError",
    "WitnessVerificationProof",
    "require_witness_verification",
    "verify_witness_bundle",
]
