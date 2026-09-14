"""
GerChain V78.3
Atomic Settlement Engine.

Purpose:
- Execute deterministic monetary settlement.
- Connect escrow state and money movement.
- Validate DEE authorization before mutation.
- Roll back state if settlement fails.
- Witness the completed settlement.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from core.hashing import domain_hash
from dee_security.root_of_trust import RootOfTrust
from dee_security.settlement_governance import SettlementAuthorization, authorize_settlement
from escrow.engine import EscrowEngine
from money.ledger import MoneyLedger
from money.record import MoneyRecord


class MoneyEngine:
    """Дижитал мөнгөний шилжилт ба DEE хамгаалалттай атомар тооцооны хөдөлгүүр."""

    def __init__(self, ledger: MoneyLedger, escrow: EscrowEngine):
        self.ledger = ledger
        self.escrow = escrow
        self.records = []

    def transfer(self, transaction_id: str, source: str, destination: str, amount: int, timestamp: str, evidence: Any) -> MoneyRecord:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")
        source_balance = self.ledger.get_balance(source)
        destination_balance = self.ledger.get_balance(destination)
        if source_balance < amount:
            raise ValueError("Insufficient balance.")
        sequence = len(self.records) + 1
        new_source_balance = source_balance - amount
        new_destination_balance = destination_balance + amount
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
        transfer_hash = domain_hash("MONEY_TRANSFER", transfer_obj)
        old_balances = copy.deepcopy(self.ledger.balances)
        old_records_length = len(self.records)
        witness_chain = self.escrow.witness_chain
        witness_checkpoint = witness_chain._checkpoint()
        try:
            witness_record = witness_chain.append_event(
                event_id=f"MONEY-{transaction_id}-{sequence}",
                event_type="MONEY_TRANSFER",
                timestamp=timestamp,
                payload=transfer_obj,
                evidence=evidence,
            )
            self.ledger.transfer(source, destination, amount)
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
        except Exception:
            self.ledger.balances = old_balances
            if len(self.records) > old_records_length:
                self.records = self.records[:old_records_length]
            witness_chain._restore(witness_checkpoint)
            raise

    def atomic_settlement(
        self,
        transaction_id: str,
        target_state: str,
        source: str,
        destination: str,
        amount: int,
        timestamp: str,
        evidence: Any,
        *,
        root: RootOfTrust | None = None,
        owner_id: str | None = None,
        authorized: bool = False,
        evidence_verified: bool = False,
        trinity_proof: Mapping[str, bool] | None = None,
    ) -> MoneyRecord:
        """Settle money and terminal escrow state only after DEE governance passes."""
        if root is None or owner_id is None or trinity_proof is None:
            raise ValueError("DEE Root of Trust and Trinity proof are required for atomic settlement")
        if self.escrow.state["state"] != "LOCKED":
            raise ValueError("Settlement requires LOCKED escrow.")
        if amount <= 0:
            raise ValueError("Settlement amount must be positive.")
        if amount != self.escrow.amount:
            raise ValueError("Settlement amount must equal escrow amount.")
        if target_state not in {"RELEASED", "REFUNDED"}:
            raise ValueError("Atomic settlement target must be RELEASED or REFUNDED.")

        authorize_settlement(
            root=root,
            authorization=SettlementAuthorization(
                transaction_id=transaction_id,
                escrow_id=self.escrow.escrow_id,
                owner_id=owner_id,
                authorized=authorized,
                evidence_verified=evidence_verified,
            ),
            trinity_proof=trinity_proof,
        )

        source_balance = self.ledger.get_balance(source)
        if source_balance < amount:
            raise ValueError("Insufficient escrow balance.")

        old_balances = copy.deepcopy(self.ledger.balances)
        old_escrow_state = copy.deepcopy(self.escrow.state)
        old_records_length = len(self.records)
        witness_chain = self.escrow.witness_chain
        witness_checkpoint = witness_chain._checkpoint()

        try:
            sequence = len(self.records) + 1
            new_source_balance = source_balance - amount
            destination_balance = self.ledger.get_balance(destination)
            new_destination_balance = destination_balance + amount
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
            settlement_hash = domain_hash("ATOMIC_SETTLEMENT", settlement_obj)
            witness_record = witness_chain.append_event(
                event_id=f"SETTLEMENT-{transaction_id}-{sequence}",
                event_type="ATOMIC_SETTLEMENT",
                timestamp=timestamp,
                payload=settlement_obj,
                evidence=evidence,
            )
            self.ledger.transfer(source, destination, amount)
            # DEE/G-3 authorization is already the governing boundary above.
            # EscrowEngine owns only the deterministic lifecycle transition.
            self.escrow.transition(target_state, timestamp, evidence)
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
                self.records = self.records[:old_records_length]
            witness_chain._restore(witness_checkpoint)
            raise


__all__ = ["MoneyEngine"]
