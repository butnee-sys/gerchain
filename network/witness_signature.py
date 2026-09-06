"""
GerChain V84.1
Ed25519 Witness Signature.

Principles:
- Private key is used only for signing.
- Public key is sufficient for independent verification.
- Verifier never receives the private key.
- Signature verification is deterministic.
- V84.0 HMAC protection remains unchanged.
"""

from __future__ import annotations

import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


class WitnessSignature:
    VERSION = "V84.1"

    def __init__(
        self,
        private_key: Ed25519PrivateKey,
    ):
        if not isinstance(
            private_key,
            Ed25519PrivateKey,
        ):
            raise TypeError(
                "private_key must be an Ed25519PrivateKey."
            )

        self._private_key = private_key

    @classmethod
    def generate(cls) -> "WitnessSignature":
        return cls(
            Ed25519PrivateKey.generate()
        )

    def public_key_bytes(self) -> bytes:
        return self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def public_id(self) -> str:
        return hashlib.sha256(
            self.public_key_bytes()
        ).hexdigest()

    def sign(
        self,
        payload: bytes,
    ) -> bytes:
        if not isinstance(payload, bytes):
            raise TypeError(
                "payload must be bytes."
            )

        return self._private_key.sign(payload)

    @staticmethod
    def verify(
        public_key_bytes: bytes,
        payload: bytes,
        signature: bytes,
    ) -> bool:
        if not isinstance(public_key_bytes, bytes):
            return False

        if not isinstance(payload, bytes):
            return False

        if not isinstance(signature, bytes):
            return False

        try:
            public_key = Ed25519PublicKey.from_public_bytes(
                public_key_bytes
            )

            public_key.verify(
                signature,
                payload,
            )

            return True

        except Exception:
            return False


__all__ = [
    "WitnessSignature",
]