from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import record_witness_in_transaction
from persistence.durable_idempotency import begin_in_transaction, complete_in_transaction
from persistence.transactional_outbox import deterministic_event_id, enqueue_in_transaction


class SettlementCoordinator:
    """Coordinates settlement while delegating all value truth to Canonical Ledger.

    Settlement is not an Escrow lifecycle transition. Its evidence aggregate is
    therefore the settlement transaction_id itself, while Ledger remains the
    sole value authority.
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
        payload = {
            "operation": "SETTLEMENT",
            "transaction_id": transaction_id,
            "source": source,
            "destination": destination,
            "amount": amount,
            "currency": currency,
        }
        replay = begin_in_transaction(
            self.session,
            key=transaction_id,
            payload=payload,
        )
        if replay is not None:
            return {"replayed": True, "result": replay}

        integrity_material = json.dumps(
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
        integrity_hash = hashlib.sha256(integrity_material.encode("utf-8")).hexdigest()

        result = PostgreSQLAtomicLedger.transfer_in_transaction(
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
        record_witness_in_transaction(
            self.session,
            transaction_id=transaction_id,
            event_type="GERCHAIN_SETTLEMENT",
            escrow_id=transaction_id,
            amount=amount,
        )
        enqueue_in_transaction(
            self.session,
            event_id=deterministic_event_id("GERCHAIN_SETTLEMENT", transaction_id),
            event_type="GERCHAIN_SETTLEMENT",
            aggregate_id=transaction_id,
            payload=payload,
        )
        complete_in_transaction(
            self.session,
            key=transaction_id,
            payload=payload,
            result_json=json.dumps(result, sort_keys=True, separators=(",", ":")),
        )
        return result


__all__ = ["SettlementCoordinator"]
