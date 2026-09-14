"""Deterministic idempotency guard for authoritative value-flow requests.

This component is a control capability, not a value-movement engine.  It
records a request fingerprint and its terminal result so a retried request
cannot execute the same economic mutation twice.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


class IdempotencyConflictError(ValueError):
    """Raised when one key is reused for a materially different request."""


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    fingerprint: str
    result: Any


class IdempotencyEngine:
    """Fail-closed request deduplication for one authoritative runtime."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    @staticmethod
    def fingerprint(payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def begin(self, key: str, payload: Mapping[str, Any]) -> Any | None:
        if not key:
            raise ValueError("idempotency key is required")

        fingerprint = self.fingerprint(payload)
        existing = self._records.get(key)
        if existing is None:
            return None
        if existing.fingerprint != fingerprint:
            raise IdempotencyConflictError(
                f"idempotency key reused with different request: {key}"
            )
        return existing.result

    def complete(
        self,
        key: str,
        payload: Mapping[str, Any],
        result: Any,
    ) -> Any:
        if not key:
            raise ValueError("idempotency key is required")
        fingerprint = self.fingerprint(payload)
        existing = self._records.get(key)
        if existing is not None:
            if existing.fingerprint != fingerprint:
                raise IdempotencyConflictError(
                    f"idempotency key reused with different request: {key}"
                )
            return existing.result
        self._records[key] = IdempotencyRecord(
            key=key,
            fingerprint=fingerprint,
            result=result,
        )
        return result

    def contains(self, key: str) -> bool:
        return key in self._records


__all__ = [
    "IdempotencyConflictError",
    "IdempotencyEngine",
    "IdempotencyRecord",
]
