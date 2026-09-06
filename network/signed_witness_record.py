"""
GerChain V84.4
Signed Witness Record.

Binds:
    node_id
    public_key
    binding_hash
    payload
    signature

Principles:
- The complete witness record is canonically serialized.
- The canonical record is signed with Ed25519.
- Verification uses only public information.
- Private keys never enter the record.
- Any modification to identity or payload invalidates the signature.
- Authorization remains a separate requirement.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from network.authorization import AuthorizedWitnessRegistry
from network.witness_identity import WitnessIdentity
from network.witness_signature import WitnessSignature


class SignedWitnessRecord:
    VERSION = "V84.4"

    def __init__(
        self,
        identity: WitnessIdentity,
        payload: bytes,
        signature: bytes,
    ):
        if not isinstance(identity, WitnessIdentity):
            raise TypeError(
                "identity must be a WitnessIdentity."
            )

        if not isinstance(payload, bytes):
            raise TypeError(
                "payload must be bytes."
            )

        if not isinstance(signature, bytes):
            raise TypeError(
                "signature must be bytes."
            )

        self.identity = identity
        self.payload = payload
        self.signature = signature

    @classmethod
    def create(
        cls,
        identity: WitnessIdentity,
        witness: WitnessSignature,
        payload: bytes,
    ) -> "SignedWitnessRecord":
        if not isinstance(
            witness,
            WitnessSignature,
        ):
            raise TypeError(
                "witness must be a WitnessSignature."
            )

        if not isinstance(payload, bytes):
            raise TypeError(
                "payload must be bytes."
            )

        unsigned = cls(
            identity,
            payload,
            b"",
        )

        signature = witness.sign(
            unsigned.canonical_payload()
        )

        return cls(
            identity,
            payload,
            signature,
        )

    def canonical_payload(self) -> bytes:
        record = {
            "version": self.VERSION,
            "node_id": self.identity.node_id,
            "public_key": self.identity.public_key.hex(),
            "binding_hash": self.identity.binding_hash(),
            "payload": self.payload.hex(),
        }

        return json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def record_hash(self) -> str:
        return hashlib.sha256(
            self.canonical_payload()
        ).hexdigest()

    def verify_signature(self) -> bool:
        return WitnessSignature.verify(
            self.identity.public_key,
            self.canonical_payload(),
            self.signature,
        )

    def verify_identity(self) -> bool:
        expected_identity = WitnessIdentity(
            self.identity.node_id,
            self.identity.public_key,
        )

        return (
            expected_identity.binding_hash()
            == self.identity.binding_hash()
        )

    def verify_authorization(
        self,
        registry: AuthorizedWitnessRegistry,
    ) -> bool:
        if not isinstance(
            registry,
            AuthorizedWitnessRegistry,
        ):
            return False

        return registry.is_authorized(
            self.identity.node_id
        )

    def verify(
        self,
        registry: AuthorizedWitnessRegistry,
    ) -> Dict[str, Any]:
        authorized = self.verify_authorization(
            registry
        )

        identity_valid = self.verify_identity()

        signature_valid = self.verify_signature()

        accepted = (
            authorized
            and identity_valid
            and signature_valid
        )

        return {
            "version": self.VERSION,
            "node_id": self.identity.node_id,
            "authorized": authorized,
            "identity_valid": identity_valid,
            "signature_valid": signature_valid,
            "accepted": accepted,
            "record_hash": self.record_hash(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "node_id": self.identity.node_id,
            "public_key": self.identity.public_key.hex(),
            "binding_hash": self.identity.binding_hash(),
            "payload": self.payload.hex(),
            "signature": self.signature.hex(),
            "record_hash": self.record_hash(),
        }


__all__ = [
    "SignedWitnessRecord",
]