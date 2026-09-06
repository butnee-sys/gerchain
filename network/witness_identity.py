"""
GerChain V84.2
Witness Identity Binding.

Binds a stable witness/node identifier to an
Ed25519 public key without exposing the private key.

Principles:
- Witness ID is explicitly bound to a public key.
- Binding is deterministic.
- Private keys never enter the binding object.
- A changed witness ID or public key invalidates the binding.
- This module does not replace V83.2 authorization.
- This module does not replace V84.1 signatures.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from network.witness_signature import WitnessSignature


class WitnessIdentity:
    VERSION = "V84.2"

    def __init__(
        self,
        node_id: str,
        public_key: bytes,
    ):
        if not isinstance(node_id, str):
            raise TypeError("node_id must be a string.")

        if not node_id:
            raise ValueError("node_id cannot be empty.")

        if not isinstance(public_key, bytes):
            raise TypeError("public_key must be bytes.")

        if len(public_key) != 32:
            raise ValueError(
                "Ed25519 public_key must be 32 bytes."
            )

        self.node_id = node_id
        self.public_key = public_key

    @classmethod
    def from_witness(
        cls,
        node_id: str,
        witness: WitnessSignature,
    ) -> "WitnessIdentity":
        if not isinstance(
            witness,
            WitnessSignature,
        ):
            raise TypeError(
                "witness must be a WitnessSignature."
            )

        return cls(
            node_id,
            witness.public_key_bytes(),
        )

    def binding_payload(self) -> bytes:
        payload = {
            "version": self.VERSION,
            "node_id": self.node_id,
            "public_key": self.public_key.hex(),
        }

        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def binding_hash(self) -> str:
        return hashlib.sha256(
            self.binding_payload()
        ).hexdigest()

    def verify_signature(
        self,
        payload: bytes,
        signature: bytes,
    ) -> bool:
        return WitnessSignature.verify(
            self.public_key,
            payload,
            signature,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "node_id": self.node_id,
            "public_key": self.public_key.hex(),
            "binding_hash": self.binding_hash(),
        }


__all__ = [
    "WitnessIdentity",
]