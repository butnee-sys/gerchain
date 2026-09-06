"""
GerChain V84.3
Authorized Witness Identity Binding.

Connects:
    node_id
    public key
    authorized witness registry
    Ed25519 signature

Principles:
- Only authorized node IDs may be accepted.
- The node ID must be cryptographically bound to its public key.
- The signature must verify against that public key.
- Private keys are never exposed to the verifier.
- V83.2 authorization remains unchanged.
- V84.1 signature verification remains unchanged.
- V84.2 identity binding remains unchanged.
"""

from __future__ import annotations

from typing import Any, Dict

from network.authorization import AuthorizedWitnessRegistry
from network.witness_identity import WitnessIdentity


class AuthorizedWitnessIdentity:
    VERSION = "V84.3"

    def __init__(
        self,
        registry: AuthorizedWitnessRegistry,
        identity: WitnessIdentity,
    ):
        if not isinstance(
            registry,
            AuthorizedWitnessRegistry,
        ):
            raise TypeError(
                "registry must be an AuthorizedWitnessRegistry."
            )

        if not isinstance(
            identity,
            WitnessIdentity,
        ):
            raise TypeError(
                "identity must be a WitnessIdentity."
            )

        self.registry = registry
        self.identity = identity

    def is_authorized(self) -> bool:
        return self.registry.is_authorized(
            self.identity.node_id
        )

    def verify_identity_binding(
        self,
        expected_binding_hash: str,
    ) -> bool:
        if not isinstance(
            expected_binding_hash,
            str,
        ):
            return False

        return (
            self.identity.binding_hash()
            == expected_binding_hash
        )

    def verify_signature(
        self,
        payload: bytes,
        signature: bytes,
    ) -> bool:
        if not self.is_authorized():
            return False

        return self.identity.verify_signature(
            payload,
            signature,
        )

    def verify(
        self,
        payload: bytes,
        signature: bytes,
        expected_binding_hash: str,
    ) -> Dict[str, Any]:
        authorized = self.is_authorized()
        binding_valid = self.verify_identity_binding(
            expected_binding_hash
        )

        signature_valid = False

        if authorized and binding_valid:
            signature_valid = self.verify_signature(
                payload,
                signature,
            )

        accepted = (
            authorized
            and binding_valid
            and signature_valid
        )

        return {
            "version": self.VERSION,
            "node_id": self.identity.node_id,
            "authorized": authorized,
            "binding_valid": binding_valid,
            "signature_valid": signature_valid,
            "accepted": accepted,
        }


__all__ = [
    "AuthorizedWitnessIdentity",
]