"""
GerChain V78.2
Atomic Settlement Engine.

Purpose:
- Execute deterministic monetary settlement.
- Connect escrow state and money movement.
- Validate all conditions before mutation.
- Roll back state if settlement fails.
- Witness the completed settlement.
"""

from __future__ import annotations

import copy
from typing import Any

from core.hashing import domain_hash
from escrow.engine import EscrowEngine
from money.ledger import MoneyLedger
from money.record import MoneyRecord


class MoneyEngine:
    """Дижитал мөнгөний шилжилт ба атомар тооцооны хөдөлгүүр."""

    def __init__(
        self,
        ledger: MoneyLedger,
        escrow: EscrowEngine,
    ):
        self.ledger = ledger
        self.escrow = escrow
        self.records = []

    def transfer(
        self,
        transaction_id: str,
        source: str,
        destination: str,
        amount: int,
        timestamp: str,
        evidence: Any,
    ) -> MoneyRecord:

        if amount <= 0:
            raise ValueError(
                "Transfer amount must be positive."
            )

        source_balance = self.ledger.get_balance(source)
        destination_balance = self.ledger.get_balance(destination)

        if source_balance < amount:
            raise ValueError(
                "Insufficient balance."
            )

        sequence = len(self.records) + 1

        new_source_balance = source_balance - amount
        new_destination_balance = (
            destination_balance + amount
        )

        transfer_obj = {
            "transaction_id": transaction_id,
            "sequence": sequence,
            "source": source,
            "destination": destination,
            "amount": amount,
            "currency": self.ledger.currency,
            "previous_source_balance": source_balance,
            "new_source_balance": new_source_balance,
            "previous_destination_balance": destination_balance,
            "new_destination_balance": new_destination_balance,
        }

        transfer_hash = domain_hash(
            "MONEY_TRANSFER",
            transfer_obj,
        )

        witness_record = self.escrow.witness_chain.append_event(
            event_id=f"MONEY-{transaction_id}-{sequence}",
            event_type="MONEY_TRANSFER",
            timestamp=timestamp,
            payload=transfer_obj,
            evidence=evidence,
        )

        self.ledger.transfer(
            source,
            destination,
            amount,
        )

        record = MoneyRecord(
            transaction_id=transaction_id,
            sequence=sequence,
            source=source,
            destination=destination,
            amount=amount,
            currency=self.ledger.currency,
            previous_source_balance=source_balance,
            new_source_balance=new_source_balance,
            previous_destination_balance=destination_balance,
            new_destination_balance=new_destination_balance,
            transfer_hash=transfer_hash,
            witness_event_hash=witness_record.event_hash,
            witness_id=witness_record.witness_id,
        )

        self.records.append(record)

        return record

    def atomic_settlement(
        self,
        transaction_id: str,
        target_state: str,
        source: str,
        destination: str,
        amount: int,
        timestamp: str,
        evidence: Any,
    ) -> MoneyRecord:

        if amount <= 0:
            raise ValueError(
                "Settlement amount must be positive."
            )

        if self.escrow.state["state"] != "LOCKED":
            raise ValueError(
                "Settlement requires LOCKED escrow."
            )

        if amount != self.escrow.amount:
            raise ValueError(
                "Settlement amount must equal escrow amount."
            )

        if target_state == "RELEASED":
            expected_destination = destination
        elif target_state == "REFUNDED":
            expected_destination = destination
        else:
            raise ValueError(
                "Atomic settlement target must be "
                "RELEASED or REFUNDED."
            )

        if destination != expected_destination:
            raise ValueError(
                "Invalid settlement destination."
            )

        source_balance = self.ledger.get_balance(source)

        if source_balance < amount:
            raise ValueError(
                "Insufficient escrow balance."
            )

        old_balances = copy.deepcopy(
            self.ledger.balances
        )

        old_escrow_state = copy.deepcopy(
            self.escrow.state
        )

        old_records_length = len(self.records)

        try:
            sequence = len(self.records) + 1

            new_source_balance = source_balance - amount

            destination_balance = (
                self.ledger.get_balance(destination)
            )

            new_destination_balance = (
                destination_balance + amount
            )

            settlement_obj = {
                "transaction_id": transaction_id,
                "sequence": sequence,
                "source": source,
                "destination": destination,
                "amount": amount,
                "currency": self.ledger.currency,
                "escrow_id": self.escrow.escrow_id,
                "previous_escrow_state": "LOCKED",
                "new_escrow_state": target_state,
                "previous_source_balance": source_balance,
                "new_source_balance": new_source_balance,
                "previous_destination_balance": destination_balance,
                "new_destination_balance": new_destination_balance,
            }

            settlement_hash = domain_hash(
                "ATOMIC_SETTLEMENT",
                settlement_obj,
            )

            witness_record = (
                self.escrow.witness_chain.append_event(
                    event_id=(
                        f"SETTLEMENT-"
                        f"{transaction_id}-"
                        f"{sequence}"
                    ),
                    event_type="ATOMIC_SETTLEMENT",
                    timestamp=timestamp,
                    payload=settlement_obj,
                    evidence=evidence,
                )
            )

            self.ledger.transfer(
                source,
                destination,
                amount,
            )

            self.escrow.transition(
                target_state,
                timestamp,
                evidence,
            )

            record = MoneyRecord(
                transaction_id=transaction_id,
                sequence=sequence,
                source=source,
                destination=destination,
                amount=amount,
                currency=self.ledger.currency,
                previous_source_balance=source_balance,
                new_source_balance=new_source_balance,
                previous_destination_balance=destination_balance,
                new_destination_balance=new_destination_balance,
                transfer_hash=settlement_hash,
                witness_event_hash=witness_record.event_hash,
                witness_id=witness_record.witness_id,
            )

            self.records.append(record)

            return record

        except Exception:
            self.ledger.balances = old_balances
            self.escrow.state = old_escrow_state

            if len(self.records) > old_records_length:
                self.records = self.records[
                    :old_records_length
                ]

            raise


__all__ = [
    "MoneyEngine",
]