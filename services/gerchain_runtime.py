"""
GerChain Runtime
================

Gerchain Core-ийн authoritative runtime boundary.

Architecture:

    API / Dashboard
          |
          v
    GerchainRuntime
          |
          +-- WitnessChain
          +-- MoneyLedger
          +-- EscrowEngine
          +-- MoneyEngine
          +-- AuthoritativeEscrowService
          +-- V80IndependentVerifier

Principle:

    Core state = authoritative
    Database   = projection / query layer
    Dashboard  = presentation / API layer
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from services.authoritative_escrow import (
    AuthoritativeEscrowService,
)
from verifier.v80_independent_verifier import (
    V80IndependentVerifier,
)
from witness.chain import WitnessChain


class GerchainRuntime:
    """
    Gerchain Core-ийн нэг authoritative runtime.

    Нэг runtime дотор:
      - WitnessChain
      - MoneyLedger
      - EscrowEngine
      - MoneyEngine
      - AuthoritativeEscrowService
      - V80IndependentVerifier

    бүгд нэг Core төлөв дээр ажиллана.
    """

    def __init__(
        self,
        *,
        escrow_id: str,
        amount: int,
        currency: str,
        witness_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
        manifest: Optional[Dict[str, Any]] = None,
        initial_money_state: Optional[
            Dict[str, Any]
        ] = None,
    ):
        if not escrow_id:
            raise ValueError(
                "escrow_id is required"
            )

        if amount <= 0:
            raise ValueError(
                "Escrow amount must be positive."
            )

        if not currency:
            raise ValueError(
                "currency is required"
            )

        if not witness_id:
            raise ValueError(
                "witness_id is required"
            )

        if initial_state is None:
            initial_state = {
                "escrow_id": escrow_id,
                "state": "CREATED",
                "amount": amount,
                "currency": currency,
                "transition_counter": 0,
            }

        if manifest is None:
            manifest = {
                "runtime": "GerchainRuntime",
                "version": "1.0.0",
                "currency": currency,
                "escrow_id": escrow_id,
            }

        self.witness_chain = WitnessChain(
            initial_state=initial_state,
            manifest=manifest,
            witness_id=witness_id,
            initial_money_state=initial_money_state,
        )

        # V80.4.3:
        # Initial Money State-ийг authoritative Witness event
        # болгон chain-ийн эхэнд бүртгэнэ.
        if initial_money_state is not None:
            commitment = (
                self.witness_chain
                .get_initial_money_commitment()
            )

            self.witness_chain.append_event(
                event_id=(
                    f"INITIAL-MONEY-{escrow_id}"
                ),
                event_type="INITIAL_MONEY_STATE",
                timestamp="GENESIS",
                payload={
                    "state": commitment["state"],
                    "state_hash": commitment["state_hash"],
                },
                evidence={
                    "type": "INITIAL_MONEY_COMMITMENT",
                    "reference": (
                        f"INITIAL-MONEY-{escrow_id}"
                    ),
                },
            )

        self.money_ledger = MoneyLedger(
            currency=currency
        )

        self.escrow_engine = EscrowEngine(
            escrow_id=escrow_id,
            amount=amount,
            currency=currency,
            witness_chain=self.witness_chain,
        )

        self.money_engine = MoneyEngine(
            ledger=self.money_ledger,
            escrow=self.escrow_engine,
        )

        self.verifier = V80IndependentVerifier()

        self.escrow_service = (
            AuthoritativeEscrowService(
                escrow_engine=self.escrow_engine,
                money_engine=self.money_engine,
                verifier=self.verifier,
            )
        )

    # -------------------------------------------------
    # Accounts
    # -------------------------------------------------

    def create_account(
        self,
        account_id: str,
        initial_balance: int = 0,
    ) -> None:
        """
        Core authoritative money account үүсгэнэ.
        """

        self.money_ledger.create_account(
            account_id=account_id,
            initial_balance=initial_balance,
        )

    def verify_initial_money_consistency(self) -> bool:
        """
        Authoritative Initial Money State болон
        operational MoneyLedger-ийн нийцлийг шалгана.

        Currency, account set, balance гурав яг
        таарч байж зөвшөөрнө.
        """

        commitment = (
            self.witness_chain
            .get_initial_money_commitment()
        )

        if commitment is None:
            raise ValueError(
                "Initial money state commitment is required."
            )

        authoritative_state = commitment.get("state")

        if not isinstance(authoritative_state, dict):
            raise ValueError(
                "Initial money state must be a dictionary."
            )

        authoritative_currency = (
            authoritative_state.get("currency")
        )
        authoritative_balances = (
            authoritative_state.get("balances")
        )

        if not authoritative_currency:
            raise ValueError(
                "Initial money state currency is required."
            )

        if not isinstance(authoritative_balances, dict):
            raise ValueError(
                "Initial money state balances must be a dictionary."
            )

        if self.money_ledger.currency != authoritative_currency:
            raise ValueError(
                "Initial money state currency mismatch."
            )

        if set(self.money_ledger.balances) != set(
            authoritative_balances
        ):
            raise ValueError(
                "Initial money state account set mismatch."
            )

        if self.money_ledger.balances != authoritative_balances:
            raise ValueError(
                "Initial money state balance mismatch."
            )

        return True

    def get_balance(
        self,
        account_id: str,
    ) -> int:
        """
        Core authoritative balance.
        """

        return self.money_ledger.get_balance(
            account_id
        )

    # -------------------------------------------------
    # Escrow
    # -------------------------------------------------

    def get_escrow_state(self) -> Dict[str, Any]:
        """
        Core authoritative escrow state.
        """

        return self.escrow_service.get_state()

    def fund(
        self,
        *,
        transaction_id: str,
        source: str,
        timestamp: str,
        evidence: Any,
    ):
        """
        CREATED -> FUNDED

        Мөнгө source account-аас escrow account
        руу шилжинэ.
        """

        return self.escrow_service.fund(
            transaction_id=transaction_id,
            source=source,
            timestamp=timestamp,
            evidence=evidence,
        )

    def lock(
        self,
        *,
        transaction_id: str,
        timestamp: str,
        evidence: Any,
    ):
        """
        FUNDED -> LOCKED
        """

        return self.escrow_service.lock(
            transaction_id=transaction_id,
            timestamp=timestamp,
            evidence=evidence,
        )

    def release(
        self,
        *,
        transaction_id: str,
        destination: str,
        timestamp: str,
        evidence: Any,
    ):
        """
        LOCKED -> RELEASED

        Мөнгө escrow account-аас destination
        account руу атомар шилжинэ.
        """

        return self.escrow_service.release(
            transaction_id=transaction_id,
            destination=destination,
            timestamp=timestamp,
            evidence=evidence,
        )

    def refund(
        self,
        *,
        transaction_id: str,
        destination: str,
        timestamp: str,
        evidence: Any,
    ):
        """
        LOCKED -> REFUNDED

        Мөнгө escrow account-аас refund destination
        account руу атомар шилжинэ.
        """

        return self.escrow_service.refund(
            transaction_id=transaction_id,
            destination=destination,
            timestamp=timestamp,
            evidence=evidence,
        )

    # -------------------------------------------------
    # Verification
    # -------------------------------------------------

    def serialize(self) -> bytes:
        """
        Одоогийн WitnessChain-ийг canonical bundle
        болгон сериализлана.
        """

        from persistence.serializer import (
            serialize_chain,
        )

        return serialize_chain(
            self.witness_chain
        )

    def verify(self) -> bool:
        """
        Одоогийн Core bundle-ийг V80 бие даасан
        шалгагчаар шалгана.
        """

        return self.verifier.verify_bytes(
            self.serialize()
        )

    def verify_report(self) -> Dict[str, Any]:
        """
        Одоогийн Core bundle-ийн дэлгэрэнгүй
        бие даасан шалгалтын тайлан.
        """

        return self.verifier.verify_with_report(
            self._bundle()
        )

    def _bundle(self) -> Dict[str, Any]:
        """
        Canonical serializer-тэй ижил bundle
        бүтэц үүсгэнэ.

        Энэ нь verifier report-д зориулсан дотоод
        representation юм.
        """

        return {
            "manifest": self.witness_chain.manifest,
            "manifest_hash": (
                self.witness_chain.manifest_hash
            ),
            "witness_id": (
                self.witness_chain.witness_id
            ),
            "initial_state": (
                self.witness_chain.initial_state
            ),
            "entries": [
                {
                    "record": {
                        "sequence": (
                            entry.record.sequence
                        ),
                        "event_id": (
                            entry.record.event_id
                        ),
                        "event_type": (
                            entry.record.event_type
                        ),
                        "timestamp": (
                            entry.record.timestamp
                        ),
                        "previous_state_hash": (
                            entry.record.previous_state_hash
                        ),
                        "event_hash": (
                            entry.record.event_hash
                        ),
                        "new_state_hash": (
                            entry.record.new_state_hash
                        ),
                        "evidence_hash": (
                            entry.record.evidence_hash
                        ),
                        "witness_id": (
                            entry.record.witness_id
                        ),
                        "manifest_hash": (
                            entry.record.manifest_hash
                        ),
                    },
                    "event_payload": (
                        entry.event_payload
                    ),
                    "evidence": entry.evidence,
                }
                for entry in self.witness_chain.entries
            ],
        }


__all__ = [
    "GerchainRuntime",
]
