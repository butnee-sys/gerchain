from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger


class SettlementCoordinator:
    """Coordinates settlement while delegating all value truth to Canonical Ledger."""

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
        return PostgreSQLAtomicLedger.transfer_in_transaction(
            self.session,
            transaction_id=transaction_id,
            source=source,
            destination=destination,
            amount=amount,
            currency=currency,
        )


__all__ = ["SettlementCoordinator"]
