from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from core.idempotency import IdempotencyEngine


@dataclass(frozen=True)
class EscrowTransaction:
    transaction_id: str
    escrow_id: str
    source: str
    destination: str
    amount: int
    currency: str
    state: str
    witness_id: str
    event_hash: str | None = None
    witness_event_hash: str | None = None


class AuthoritativeEscrowService:
    """
    Gerchain-ийн authoritative transaction boundary.

    UI/API database-д мөнгө болон escrow state-ийг
    шууд өөрчлөхгүй.

    Бүх mutation Core engine-ээр хийгдэнэ.
    Idempotency нь mutation boundary дээр давхар хөдөлгөөнөөс хамгаална.
    """

    def __init__(
        self,
        escrow_engine,
        money_engine,
        verifier,
        idempotency: IdempotencyEngine | None = None,
    ):
        self.escrow = escrow_engine
        self.money = money_engine
        self.verifier = verifier
        self.idempotency = idempotency or IdempotencyEngine()

    def get_state(self) -> dict[str, Any]:
        return dict(self.escrow.state)

    def get_balance(self, account_id: str) -> int:
        return self.money.ledger.get_balance(account_id)

    def fund(
        self,
        transaction_id: str,
        source: str,
        timestamp: str,
        evidence: Any,
    ) -> EscrowTransaction:
        if not transaction_id:
            raise ValueError("transaction_id is required")

        key = f"fund:{transaction_id}"
        payload = {
            "operation": "fund",
            "transaction_id": transaction_id,
            "source": source,
            "timestamp": timestamp,
            "evidence": evidence,
        }
        replay = self.idempotency.begin(key, payload)
        if replay is not None:
            return replay

        state = self.escrow.state["state"]
        if state != "CREATED":
            raise ValueError(f"Funding requires CREATED escrow, got {state}")

        amount = self.escrow.amount
        escrow_account = self.escrow.escrow_id

        try:
            self.money.ledger.get_balance(escrow_account)
        except ValueError as exc:
            raise ValueError(
                f"Escrow account does not exist: {escrow_account}"
            ) from exc

        ledger_checkpoint = dict(self.money.ledger.balances)
        money_records_checkpoint = len(self.money.records)
        escrow_state_checkpoint = copy.deepcopy(self.escrow.state)
        escrow_records_checkpoint = len(self.escrow.records)
        witness_checkpoint = self.escrow.witness_chain._checkpoint()

        try:
            self.money.transfer(
                transaction_id=transaction_id,
                source=source,
                destination=escrow_account,
                amount=amount,
                timestamp=timestamp,
                evidence=evidence,
            )

            self.escrow.transition(
                target_state="FUNDED",
                timestamp=timestamp,
                evidence=evidence,
            )

            result = self._snapshot(transaction_id)
            return self.idempotency.complete(key, payload, result)

        except Exception:
            self.money.ledger.balances = dict(ledger_checkpoint)
            del self.money.records[money_records_checkpoint:]
            self.escrow.state = copy.deepcopy(escrow_state_checkpoint)
            del self.escrow.records[escrow_records_checkpoint:]
            self.escrow.witness_chain._restore(witness_checkpoint)
            raise

    def lock(
        self,
        transaction_id: str,
        timestamp: str,
        evidence: Any,
    ) -> EscrowTransaction:
        if not transaction_id:
            raise ValueError("transaction_id is required")

        key = f"lock:{transaction_id}"
        payload = {
            "operation": "lock",
            "transaction_id": transaction_id,
            "timestamp": timestamp,
            "evidence": evidence,
        }
        replay = self.idempotency.begin(key, payload)
        if replay is not None:
            return replay

        state = self.escrow.state["state"]
        if state != "FUNDED":
            raise ValueError(f"Lock requires FUNDED escrow, got {state}")

        self.escrow.transition(
            target_state="LOCKED",
            timestamp=timestamp,
            evidence=evidence,
        )

        result = self._snapshot(transaction_id)
        return self.idempotency.complete(key, payload, result)

    def release(
        self,
        transaction_id: str,
        destination: str,
        timestamp: str,
        evidence: Any,
    ) -> EscrowTransaction:
        if not transaction_id:
            raise ValueError("transaction_id is required")

        key = f"release:{transaction_id}"
        payload = {
            "operation": "release",
            "transaction_id": transaction_id,
            "destination": destination,
            "timestamp": timestamp,
            "evidence": evidence,
        }
        replay = self.idempotency.begin(key, payload)
        if replay is not None:
            return replay

        state = self.escrow.state["state"]
        if state != "LOCKED":
            raise ValueError(f"Release requires LOCKED escrow, got {state}")

        amount = self.escrow.amount
        escrow_account = self.escrow.escrow_id

        record = self.money.atomic_settlement(
            transaction_id=transaction_id,
            target_state="RELEASED",
            source=escrow_account,
            destination=destination,
            amount=amount,
            timestamp=timestamp,
            evidence=evidence,
        )

        result = EscrowTransaction(
            transaction_id=transaction_id,
            escrow_id=self.escrow.escrow_id,
            source=escrow_account,
            destination=destination,
            amount=amount,
            currency=self.money.ledger.currency,
            state=self.escrow.state["state"],
            witness_id=record.witness_id,
            event_hash=record.transfer_hash,
            witness_event_hash=record.witness_event_hash,
        )
        return self.idempotency.complete(key, payload, result)

    def refund(
        self,
        transaction_id: str,
        destination: str,
        timestamp: str,
        evidence: Any,
    ) -> EscrowTransaction:
        if not transaction_id:
            raise ValueError("transaction_id is required")

        key = f"refund:{transaction_id}"
        payload = {
            "operation": "refund",
            "transaction_id": transaction_id,
            "destination": destination,
            "timestamp": timestamp,
            "evidence": evidence,
        }
        replay = self.idempotency.begin(key, payload)
        if replay is not None:
            return replay

        state = self.escrow.state["state"]
        if state != "LOCKED":
            raise ValueError(f"Refund requires LOCKED escrow, got {state}")

        amount = self.escrow.amount
        escrow_account = self.escrow.escrow_id

        record = self.money.atomic_settlement(
            transaction_id=transaction_id,
            target_state="REFUNDED",
            source=escrow_account,
            destination=destination,
            amount=amount,
            timestamp=timestamp,
            evidence=evidence,
        )

        result = EscrowTransaction(
            transaction_id=transaction_id,
            escrow_id=self.escrow.escrow_id,
            source=escrow_account,
            destination=destination,
            amount=amount,
            currency=self.money.ledger.currency,
            state=self.escrow.state["state"],
            witness_id=record.witness_id,
            event_hash=record.transfer_hash,
            witness_event_hash=record.witness_event_hash,
        )
        return self.idempotency.complete(key, payload, result)

    def verify_bundle(
        self,
        bundle: dict[str, Any],
    ) -> bool:
        return bool(self.verifier.verify_bundle(bundle))

    def _snapshot(self, transaction_id: str) -> EscrowTransaction:
        return EscrowTransaction(
            transaction_id=transaction_id,
            escrow_id=self.escrow.escrow_id,
            source="",
            destination="",
            amount=self.escrow.amount,
            currency=self.money.ledger.currency,
            state=self.escrow.state["state"],
            witness_id=self.escrow.witness_chain.witness_id,
        )
