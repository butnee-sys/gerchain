"""
GerChain V84.0
Witness Key Protection.

Principles:
- Private key is never exposed by verification.
- Signing and verification are separate operations.
- Deterministic payload is required.
- HMAC-SHA256 is used for the initial V84.0 implementation.
- This module does not replace V83.2 authorization or consensus.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets


class WitnessKey:
    VERSION = "V84.0"

    def __init__(self, private_key: bytes):
        if not isinstance(private_key, bytes):
            raise TypeError("private_key must be bytes.")

        if len(private_key) < 32:
            raise ValueError(
                "private_key must be at least 32 bytes."
            )

        self._private_key = private_key

    @classmethod
    def generate(cls) -> "WitnessKey":
        return cls(
            secrets.token_bytes(32)
        )

    def public_id(self) -> str:
        return hashlib.sha256(
            self._private_key
        ).hexdigest()

    def sign(
        self,
        payload: bytes,
    ) -> str:
        if not isinstance(payload, bytes):
            raise TypeError(
                "payload must be bytes."
            )

        return hmac.new(
            self._private_key,
            payload,
            hashlib.sha256,
        ).hexdigest()

    def verify(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        if not isinstance(payload, bytes):
            return False

        if not isinstance(signature, str):
            return False

        expected = self.sign(payload)

        return hmac.compare_digest(
            expected,
            signature,
        )


__all__ = [
    "WitnessKey",
]