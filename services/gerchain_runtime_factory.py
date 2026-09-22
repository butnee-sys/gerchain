from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import Engine, inspect

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from postgres.migrations import apply_migrations
from services.gerchain_runtime import GerchainRuntime


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    """Compatibility configuration contract for production runtime construction."""

    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


class ProductionRuntimeFactory:
    """Create the production GerChain runtime with PostgreSQL as authority."""

    @staticmethod
    def create(
        *,
        escrow_id: str,
        amount: int,
        currency: str,
        witness_id: str,
        engine: Engine,
        session_factory: Callable[[], Any],
        initial_state: dict[str, Any] | None = None,
        manifest: dict[str, Any] | None = None,
        initial_money_state: dict[str, Any] | None = None,
    ) -> GerchainRuntime:
        if engine is None or session_factory is None:
            raise ValueError("production runtime requires PostgreSQL engine and session factory")
        if engine.dialect.name != "postgresql":
            raise ValueError("production runtime requires PostgreSQL engine")
        # Bootstrap base tables first; the canonical migration extends the
        # durable escrow table with production-only fields/constraints.
        AtomicLedgerBase.metadata.create_all(engine)
        EscrowBase.metadata.create_all(engine)
        WitnessBase.metadata.create_all(engine)
        IdempotencyBase.metadata.create_all(engine)
        OutboxBase.metadata.create_all(engine)

        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "schema"
        if not migration_dir.is_dir():
            raise RuntimeError(f"canonical production migration directory not found: {migration_dir}")
        with engine.connect() as connection:
            apply_migrations(connection, migration_dir)

        required = {
            "escrows": {"id", "sender_address", "receiver_address", "amount", "state", "refund_destination", "currency", "version", "created_at", "updated_at"},
            "gerchain_ledger_accounts": {"account_id", "currency", "balance", "version", "updated_at"},
            "gerchain_ledger_movements": {"id", "transaction_id", "source", "destination", "amount", "currency", "operation", "escrow_id", "integrity_hash", "created_at"},
            "gerchain_transaction_witnesses": {"id", "transaction_id", "event_type", "escrow_id", "amount", "created_at"},
            "gerchain_outbox_events": {"id", "event_id", "event_type", "aggregate_id", "payload_json", "state", "lease_until", "attempts", "created_at", "updated_at"},
            "gerchain_idempotency_records": {"id", "key", "fingerprint", "result_json", "state", "created_at", "updated_at"},
        }
        inspector = inspect(engine)
        missing_tables = sorted(set(required) - set(inspector.get_table_names()))
        if missing_tables:
            raise RuntimeError(f"canonical production schema missing tables: {missing_tables}")
        missing_columns = {}
        for table, columns in required.items():
            actual = {column["name"] for column in inspector.get_columns(table)}
            missing = sorted(columns - actual)
            if missing:
                missing_columns[table] = missing
        if missing_columns:
            raise RuntimeError(f"canonical production schema missing columns: {missing_columns}")
        runtime = GerchainRuntime(
            escrow_id=escrow_id,
            amount=amount,
            currency=currency,
            witness_id=witness_id,
            initial_state=initial_state,
            manifest=manifest,
            initial_money_state=initial_money_state,
        )
        runtime.configure_canonical_ledger(session_factory)
        return runtime



__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]    def initialize(self) -> None:
        """Initialize the canonical PostgreSQL persistence boundary."""
        statements = [
            "CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (account_id VARCHAR(128) PRIMARY KEY, currency VARCHAR(16) NOT NULL, balance INTEGER NOT NULL CHECK (balance >= 0), version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0), updated_at TIMESTAMPTZ NOT NULL)",
            "CREATE TABLE IF NOT EXISTS gerchain_ledger_movements (id BIGSERIAL PRIMARY KEY, transaction_id VARCHAR(128) NOT NULL UNIQUE, source VARCHAR(128) NOT NULL, destination VARCHAR(128) NOT NULL, amount INTEGER NOT NULL CHECK (amount > 0), currency VARCHAR(16) NOT NULL, operation VARCHAR(32) NOT NULL, escrow_id VARCHAR(128), integrity_hash VARCHAR(128), created_at TIMESTAMPTZ NOT NULL)",
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT",
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency VARCHAR(16)",
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()",
            "ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check",
            "ALTER TABLE escrows ADD CONSTRAINT escrows_state_check CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'))",
            "CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (id BIGSERIAL PRIMARY KEY, transaction_id VARCHAR(128) NOT NULL UNIQUE, event_type VARCHAR(64) NOT NULL, escrow_id VARCHAR(255) NOT NULL, amount INTEGER NOT NULL CHECK (amount >= 0), created_at TIMESTAMPTZ NOT NULL)",
            "CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (id BIGSERIAL PRIMARY KEY, key VARCHAR(255) NOT NULL UNIQUE, fingerprint VARCHAR(64) NOT NULL, result_json TEXT, state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED', created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL)",
            "CREATE TABLE IF NOT EXISTS gerchain_outbox_events (id BIGSERIAL PRIMARY KEY, event_id VARCHAR(255) NOT NULL UNIQUE, event_type VARCHAR(128) NOT NULL, aggregate_id VARCHAR(255) NOT NULL, payload_json TEXT NOT NULL, state VARCHAR(32) NOT NULL DEFAULT 'PENDING', lease_until TIMESTAMPTZ, attempts INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL)
        ]
        with self.engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_claim ON gerchain_outbox_events (state, id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_lease ON gerchain_outbox_events (lease_until) WHERE state = 'PROCESSING'"))

