from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger


class SettlementCoordinator:
    """Coordinates settlement while delegating all value truth to Canonical Ledger.

    Settlement is a direct Canonical Ledger movement, not an Escrow transition.
    It therefore carries its own deterministic movement integrity binding while
    remaining free of a second balance, escrow, witness, or outbox authority.
    """

    def __init__(self, session: Session):
        self.session = session

    def settle_in_transaction(
        self,
        *,
        transaction_id: str,
        source: str,
        destination: str,
        amount: int,
        currency: str,
    ) -> dict[str, Any]:
        material = json.dumps(
            {
                "transaction_id": transaction_id,
                "operation": "SETTLEMENT",
                "escrow_id": None,
                "source": source,
                "destination": destination,
                "amount": amount,
                "currency": currency,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        integrity_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
        return PostgreSQLAtomicLedger.transfer_in_transaction(
            self.session,
            transaction_id=transaction_id,
            source=source,
            destination=destination,
            amount=amount,
            currency=currency,
            operation="SETTLEMENT",
            escrow_id=None,
            integrity_hash=integrity_hash,
        )


__all__ = ["SettlementCoordinator"]
