"""Durable verification and consumption of signed value-operation approvals."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import CHAR, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from dee_security.root_of_trust import RootOfTrust, SecurityError, SignedChange


class AuthorizationBase(DeclarativeBase):
    pass


class SignedChangeAuthorization(AuthorizationBase):
    """Append-only record proving a signed operation approval was consumed."""

    __tablename__ = "gerchain_authorization_changes"
    __table_args__ = (
        UniqueConstraint(
            "operation",
            "transaction_id",
            name="gerchain_authorization_operation_transaction_uq",
        ),
    )

    change_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False)
    operation: Mapped[str] = mapped_column(String(16), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(128), nullable=False)
    escrow_id: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SecurityError("authorization payload is not canonical JSON data") from exc


def canonical_release_payload(
    *,
    transaction_id: str,
    escrow_id: str,
    source: str,
    destination: str,
    amount: int,
    currency: str,
    decision_status: str,
    trust: bool,
    transparency: bool,
    performance: bool,
    evidence_verified: bool,
    evidence: Any,
) -> dict[str, Any]:
    """Build the exact RELEASE facts covered by the Ed25519 approval."""
    if not all(isinstance(value, str) and value for value in (
        transaction_id, escrow_id, source, destination, currency
    )):
        raise SecurityError("RELEASE authorization identifiers are required")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise SecurityError("RELEASE authorization amount must be a positive integer")
    normalized_currency = currency.upper()
    if not re.fullmatch(r"[A-Z]{3}", normalized_currency):
        raise SecurityError("RELEASE authorization currency must be an ISO 4217 code")
    if decision_status != "APPROVE":
        raise SecurityError("RELEASE authorization requires APPROVE decision")
    evidence_hash = hashlib.sha256(_canonical_json_bytes(evidence)).hexdigest()
    return {
        "schema_version": 1,
        "operation": "RELEASE",
        "transaction_id": transaction_id,
        "escrow_id": escrow_id,
        "source": source,
        "destination": destination,
        "amount": amount,
        "currency": normalized_currency,
        "expected_state": "LOCKED",
        "new_state": "RELEASED",
        "decision_status": decision_status,
        "trust": trust is True,
        "transparency": transparency is True,
        "performance": performance is True,
        "evidence_verified": evidence_verified is True,
        "evidence_hash": evidence_hash,
    }



def canonical_refund_payload(
    *,
    transaction_id: str,
    escrow_id: str,
    source: str,
    destination: str,
    amount: int,
    currency: str,
    authorized: bool,
    transparency: bool,
    dispute_or_cancellation_verified: bool,
    evidence: Any,
) -> dict[str, Any]:
    """Build the exact REFUND facts and independent refund-policy flags."""
    if not all(isinstance(value, str) and value for value in (
        transaction_id, escrow_id, source, destination, currency
    )):
        raise SecurityError("REFUND authorization identifiers are required")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise SecurityError("REFUND authorization amount must be a positive integer")
    normalized_currency = currency.upper()
    if not re.fullmatch(r"[A-Z]{3}", normalized_currency):
        raise SecurityError("REFUND authorization currency must be an ISO 4217 code")
    if authorized is not True:
        raise SecurityError("REFUND requires authorized approval")
    if transparency is not True:
        raise SecurityError("REFUND requires transparent evidence")
    if dispute_or_cancellation_verified is not True:
        raise SecurityError("REFUND requires verified dispute or cancellation evidence")
    evidence_hash = hashlib.sha256(_canonical_json_bytes(evidence)).hexdigest()
    return {
        "schema_version": 1,
        "operation": "REFUND",
        "transaction_id": transaction_id,
        "escrow_id": escrow_id,
        "source": source,
        "destination": destination,
        "amount": amount,
        "currency": normalized_currency,
        "expected_state": "LOCKED",
        "new_state": "REFUNDED",
        "authorized": True,
        "transparency": True,
        "dispute_or_cancellation_verified": True,
        "already_released": False,
        "evidence_hash": evidence_hash,
    }


def canonical_payload_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(dict(payload))).hexdigest()


def require_pinned_root(root: RootOfTrust) -> RootOfTrust:
    """Compare any supplied trust object with the deployment-pinned public key."""
    owner_id = os.environ.get("GERCHAIN_AUTH_OWNER_ID")
    public_key_b64 = os.environ.get("GERCHAIN_AUTH_PUBLIC_KEY_B64")
    if not owner_id or not public_key_b64:
        raise SecurityError(
            "GERCHAIN_AUTH_OWNER_ID and GERCHAIN_AUTH_PUBLIC_KEY_B64 must pin the trust anchor"
        )
    pinned = RootOfTrust(owner_id=owner_id, public_key_b64=public_key_b64)
    if (
        not isinstance(root, RootOfTrust)
        or root.owner_id != pinned.owner_id
        or root.public_key_b64 != pinned.public_key_b64
    ):
        raise SecurityError("supplied RootOfTrust does not match the deployment-pinned key")
    return pinned


def verify_signed_change(
    *,
    root: RootOfTrust,
    signed_change: SignedChange,
    owner_id: str,
    expected_payload: Mapping[str, Any],
) -> str:
    """Verify signer identity, Ed25519 signature, and exact operation payload."""
    if not isinstance(root, RootOfTrust) or not isinstance(signed_change, SignedChange):
        raise SecurityError("RootOfTrust and SignedChange are mandatory")
    if not owner_id or owner_id != signed_change.owner_id or owner_id != root.owner_id:
        raise SecurityError("signed change owner does not match the authorized owner")
    root.require_valid(signed_change)
    expected_hash = canonical_payload_hash(expected_payload)
    if not hmac.compare_digest(signed_change.payload_hash, expected_hash):
        raise SecurityError("signed change payload does not match the protected operation request")
    return expected_hash


def consume_signed_change_in_transaction(
    session: Session,
    *,
    root: RootOfTrust,
    signed_change: SignedChange,
    owner_id: str,
    operation: str,
    transaction_id: str,
    escrow_id: str,
    expected_payload: Mapping[str, Any],
) -> str:
    """Verify and persist one-time authorization in the caller's value transaction."""
    if operation not in {"RELEASE", "REFUND"}:
        raise SecurityError("unsupported signed authorization operation")
    if expected_payload.get("operation") != operation:
        raise SecurityError("signed authorization operation mismatch")
    if expected_payload.get("transaction_id") != transaction_id:
        raise SecurityError("signed authorization transaction mismatch")
    if expected_payload.get("escrow_id") != escrow_id:
        raise SecurityError("signed authorization escrow mismatch")
    pinned_root = require_pinned_root(root)
    digest = verify_signed_change(
        root=pinned_root,
        signed_change=signed_change,
        owner_id=owner_id,
        expected_payload=expected_payload,
    )
    session.add(
        SignedChangeAuthorization(
            change_id=signed_change.change_id,
            owner_id=signed_change.owner_id,
            operation=operation,
            transaction_id=transaction_id,
            escrow_id=escrow_id,
            version=signed_change.version,
            payload_hash=digest,
            signature=signed_change.signature,
        )
    )
    # Force PK/UNIQUE conflicts to occur before ledger mutation. The enclosing
    # SQL transaction rolls this authorization row back if value movement fails.
    session.flush()
    return digest


__all__ = [
    "AuthorizationBase",
    "SignedChangeAuthorization",
    "canonical_release_payload",
    "canonical_refund_payload",
    "canonical_payload_hash",
    "require_pinned_root",
    "verify_signed_change",
    "consume_signed_change_in_transaction",
]
