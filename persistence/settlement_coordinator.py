from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import record_witness_in_transaction
from persistence.durable_idempotency import begin_in_transaction, complete_in_transaction, get_existing_in_transaction
from persistence.transactional_outbox import deterministic_event_id, enqueue_in_transaction


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
        idempotency_payload = {
            "operation": "SETTLEMENT",
            "source": source,
            "destination": destination,
            "amount": amount,
            "currency": currency,
        }
        replay = get_existing_in_transaction(self.session, key=transaction_id, payload=idempotency_payload)
        if replay is not None:
            return {"replayed": True, "result": replay}

        begin_in_transaction(self.session, key=transaction_id, payload=idempotency_payload)

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
            event_type="GERCHAIN_SETTLED",
            escrow_id=transaction_id,
            amount=amount,
        )
        enqueue_in_transaction(
            self.session,
            event_id=deterministic_event_id("GERCHAIN_SETTLED", transaction_id),
            event_type="GERCHAIN_SETTLED",
            aggregate_id=transaction_id,
            payload={
                "transaction_id": transaction_id,
                "operation": "SETTLEMENT",
                "source": source,
                "destination": destination,
                "amount": amount,
                "currency": currency,
            },
        )
        result_json = json.dumps(result, sort_keys=True, separators=(",", ":"))
        complete_in_transaction(
            self.session,
            key=transaction_id,
            payload=idempotency_payload,
            result_json=result_json,
        )
        return {"replayed": False, "result": result}


__all__ = ["SettlementCoordinator"]
