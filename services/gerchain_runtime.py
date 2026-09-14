"""GerChain authoritative runtime boundary."""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from core.hold import Hold, HoldEngine
from core.idempotency import IdempotencyEngine
from core.limit import LimitEngine, LimitRule
from core.transaction_lifecycle import TransactionState, TransactionStateMachine
from dee_security.root_of_trust import RootOfTrust
from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from persistence.release_adapter import PostgreSQLReleaseAdapter, ReleaseRequest
from services.authoritative_escrow import AuthoritativeEscrowService
from verifier.v80_independent_verifier import V80IndependentVerifier
from witness.chain import WitnessChain


class GerchainRuntime:
    """GerChain Core-ийн authoritative runtime.

    Default construction remains an in-memory test harness. Production code
    must use ``ProductionRuntimeFactory`` so PostgreSQL is explicitly attached
    as the durable release authority.
    """

    def __init__(self, *, escrow_id: str, amount: int, currency: str, witness_id: str, initial_state: Optional[Dict[str, Any]] = None, manifest: Optional[Dict[str, Any]] = None, initial_money_state: Optional[Dict[str, Any]] = None):
        if not escrow_id:
            raise ValueError("escrow_id is required")
        if amount <= 0:
            raise ValueError("Escrow amount must be positive.")
        if not currency:
            raise ValueError("currency is required")
        if not witness_id:
            raise ValueError("witness_id is required")
        self.runtime_mode = "test-memory"
        if initial_state is None:
            initial_state = {"escrow_id": escrow_id, "state": "CREATED", "amount": amount, "currency": currency, "transition_counter": 0}
        if manifest is None:
            manifest = {"runtime": "GerchainRuntime", "version": "1.0.0", "currency": currency, "escrow_id": escrow_id}

        self.witness_chain = WitnessChain(initial_state=initial_state, manifest=manifest, witness_id=witness_id, initial_money_state=initial_money_state)
        if initial_money_state is not None:
            commitment = self.witness_chain.get_initial_money_commitment()
            self.witness_chain.append_event(event_id=f"INITIAL-MONEY-{escrow_id}", event_type="INITIAL_MONEY_STATE", timestamp="GENESIS", payload={"state": commitment["state"], "state_hash": commitment["state_hash"]}, evidence={"type": "INITIAL_MONEY_COMMITMENT", "reference": f"INITIAL-MONEY-{escrow_id}"})

        self.money_ledger = MoneyLedger(currency=currency)
        self.escrow_engine = EscrowEngine(escrow_id=escrow_id, amount=amount, currency=currency, witness_chain=self.witness_chain)
        self.money_engine = MoneyEngine(ledger=self.money_ledger, escrow=self.escrow_engine)
        self.verifier = V80IndependentVerifier()
        self.idempotency = IdempotencyEngine()
        self.escrow_service = AuthoritativeEscrowService(escrow_engine=self.escrow_engine, money_engine=self.money_engine, verifier=self.verifier, idempotency=self.idempotency)
        self._postgres_release: PostgreSQLReleaseAdapter | None = None
        self.holds = HoldEngine()
        self.limits = LimitEngine()
        self._transactions: dict[str, TransactionStateMachine] = {}

    def configure_postgres_release(self, session_factory) -> PostgreSQLReleaseAdapter:
        from persistence.atomic_release import PostgreSQLAtomicRelease
        self._postgres_release = PostgreSQLReleaseAdapter(PostgreSQLAtomicRelease(session_factory))
        self.runtime_mode = "production-postgresql"
        return self._postgres_release

    @property
    def is_postgresql_authoritative(self) -> bool:
        return self.runtime_mode == "production-postgresql" and self._postgres_release is not None

    def require_postgresql_authority(self) -> None:
        if not self.is_postgresql_authoritative:
            raise RuntimeError("PostgreSQL authoritative runtime is required for production value flow")

    def release_postgres(self, request: ReleaseRequest):
        self.require_postgresql_authority()
        return self._postgres_release.execute(request)

    def create_transaction(self, transaction_id: str) -> TransactionStateMachine:
        if not transaction_id:
            raise ValueError("transaction_id is required")
        if transaction_id in self._transactions:
            raise ValueError(f"transaction already exists: {transaction_id}")
        machine = TransactionStateMachine()
        self._transactions[transaction_id] = machine
        return machine

    def get_transaction_state(self, transaction_id: str) -> TransactionState:
        try:
            return self._transactions[transaction_id].state
        except KeyError as exc:
            raise ValueError(f"transaction not found: {transaction_id}") from exc

    def transition_transaction(self, transaction_id: str, target: TransactionState) -> TransactionState:
        try:
            machine = self._transactions[transaction_id]
        except KeyError as exc:
            raise ValueError(f"transaction not found: {transaction_id}") from exc
        return machine.transition(target)

    def configure_limit(self, *, limit_id: str, subject_id: str, max_amount: int, cumulative: bool = False) -> None:
        self.limits.add(LimitRule(limit_id=limit_id, subject_id=subject_id, currency=self.money_ledger.currency, max_amount=max_amount, cumulative=cumulative))

    def check_limit(self, *, limit_id: str, amount: int, current_amount: int = 0) -> None:
        self.limits.check(limit_id=limit_id, amount=amount, current_amount=current_amount)

    def create_hold(self, *, hold_id: str, account_id: str, amount: int, reference: str | None = None) -> Hold:
        balance = self.money_ledger.get_balance(account_id)
        available = self.holds.available(account_id, balance)
        return self.holds.create(hold_id=hold_id, account_id=account_id, amount=amount, currency=self.money_ledger.currency, available_balance=available, reference=reference)

    def release_hold(self, hold_id: str) -> Hold:
        return self.holds.release(hold_id)

    def cancel_hold(self, hold_id: str) -> Hold:
        return self.holds.cancel(hold_id)

    def create_account(self, account_id: str, initial_balance: int = 0) -> None:
        self.money_ledger.create_account(account_id=account_id, initial_balance=initial_balance)

    def verify_initial_money_consistency(self) -> bool:
        commitment = self.witness_chain.get_initial_money_commitment()
        if commitment is None:
            raise ValueError("Initial money state commitment is required.")
        authoritative_state = commitment.get("state")
        if not isinstance(authoritative_state, dict):
            raise ValueError("Initial money state must be a dictionary.")
        authoritative_currency = authoritative_state.get("currency")
        authoritative_balances = authoritative_state.get("balances")
        if not authoritative_currency:
            raise ValueError("Initial money state currency is required.")
        if not isinstance(authoritative_balances, dict):
            raise ValueError("Initial money state balances must be a dictionary.")
        if self.money_ledger.currency != authoritative_currency:
            raise ValueError("Initial money state currency mismatch.")
        if set(self.money_ledger.balances) != set(authoritative_balances):
            raise ValueError("Initial money state account set mismatch.")
        if self.money_ledger.balances != authoritative_balances:
            raise ValueError("Initial money state balance mismatch.")
        return True

    def get_balance(self, account_id: str) -> int:
        return self.money_ledger.get_balance(account_id)

    def get_escrow_state(self) -> Dict[str, Any]:
        return self.escrow_service.get_state()

    def fund(self, *, transaction_id: str, source: str, timestamp: str, evidence: Any):
        return self.escrow_service.fund(transaction_id=transaction_id, source=source, timestamp=timestamp, evidence=evidence)

    def lock(self, *, transaction_id: str, timestamp: str, evidence: Any):
        return self.escrow_service.lock(transaction_id=transaction_id, timestamp=timestamp, evidence=evidence)

    def release(self, *, transaction_id: str, destination: str, timestamp: str, evidence: Any, root: RootOfTrust | None = None, owner_id: str | None = None, authorized: bool = False, evidence_verified: bool = False, trinity_proof: Mapping[str, bool] | None = None, source: str | None = None, idempotency_key: str | None = None):
        if root is None or owner_id is None or trinity_proof is None:
            raise ValueError("DEE authorization context is required for release")
        if self.is_postgresql_authoritative:
            if not source:
                raise ValueError("source is required for PostgreSQL authoritative release")
            return self.release_postgres(ReleaseRequest(
                idempotency_key=idempotency_key or transaction_id,
                transaction_id=transaction_id,
                escrow_id=self.escrow_engine.escrow_id,
                source=source,
                destination=destination,
                amount=self.escrow_engine.amount,
                decision_status="APPROVE",
                authorization_status="AUTHORIZED" if authorized else "DENIED",
                trinity_proof=trinity_proof,
                evidence_verified=evidence_verified,
            ))
        return self.escrow_service.release(transaction_id=transaction_id, destination=destination, timestamp=timestamp, evidence=evidence, root=root, owner_id=owner_id, authorized=authorized, evidence_verified=evidence_verified, trinity_proof=trinity_proof)

    def refund(self, *, transaction_id: str, destination: str, timestamp: str, evidence: Any, root: RootOfTrust | None = None, owner_id: str | None = None, authorized: bool = False, evidence_verified: bool = False, trinity_proof: Mapping[str, bool] | None = None):
        if root is None or owner_id is None or trinity_proof is None:
            raise ValueError("DEE authorization context is required for refund")
        return self.escrow_service.refund(transaction_id=transaction_id, destination=destination, timestamp=timestamp, evidence=evidence, root=root, owner_id=owner_id, authorized=authorized, evidence_verified=evidence_verified, trinity_proof=trinity_proof)

    def serialize(self) -> bytes:
        from persistence.serializer import serialize_chain
        return serialize_chain(self.witness_chain)

    def verify(self) -> bool:
        return self.verifier.verify_bytes(self.serialize())

    def verify_report(self) -> Dict[str, Any]:
        return self.verifier.verify_with_report(self._bundle())

    def _bundle(self) -> Dict[str, Any]:
        return {"manifest": self.witness_chain.manifest, "manifest_hash": self.witness_chain.manifest_hash, "witness_id": self.witness_chain.witness_id, "initial_state": self.witness_chain.initial_state, "entries": [{"record": {"sequence": entry.record.sequence, "event_id": entry.record.event_id, "event_type": entry.record.event_type, "timestamp": entry.record.timestamp, "previous_state_hash": entry.record.previous_state_hash, "event_hash": entry.record.event_hash, "new_state_hash": entry.record.new_state_hash, "evidence_hash": entry.record.evidence_hash, "witness_id": entry.record.witness_id, "manifest_hash": entry.record.manifest_hash}, "event_payload": entry.event_payload, "evidence": entry.evidence} for entry in self.witness_chain.entries]}


__all__ = ["GerchainRuntime"]
