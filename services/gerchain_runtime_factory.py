"""Explicit production construction for the GerChain durable runtime."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from persistence.production_schema_guard import assert_canonical_production_schema
from persistence.atomic_ledger import AtomicLedgerBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.atomic_value_transaction import WitnessBase
from postgres.migrations import apply_migrations
from services.gerchain_runtime import GerchainRuntime


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


class ProductionRuntimeFactory:
    """Construct the production runtime with Canonical Ledger authority."""

    def __init__(self, config: ProductionRuntimeConfig, *, engine: Engine | None = None) -> None:
        if not config.database_url:
            raise ValueError("database_url is required")
        if not config.database_url.startswith(
            ("postgresql://", "postgresql+psycopg://")
        ):
            raise ValueError("ProductionRuntimeFactory requires PostgreSQL database URL")
        self.config = config
        self.engine = engine or create_engine(config.database_url, future=True)
        if self.engine.dialect.name != "postgresql":
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL engine")
        self.session_factory: Callable[[], Any] = sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    def initialize(self) -> None:
        """Apply canonical PostgreSQL migrations, then reconcile ORM metadata.

        Migrations own production schema history. ORM create_all is retained
        only as a defensive no-op for metadata not yet represented by a numbered migration.
        """
        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
        with self.engine.connect() as connection:
            apply_migrations(connection, migration_dir)

        for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, TransactionWitness):
            base.metadata.create_all(self.engine)
        self._migrate_escrow_schema()

    def _migrate_escrow_schema(self) -> None:
        """Bring the legacy escrow table to the canonical aggregate contract."""
        statements = [
            "CREATE TABLE IF NOT EXISTS schema_version (version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())",
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT",
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency VARCHAR(16)",
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ",
            "UPDATE escrows SET created_at = COALESCE(created_at, updated_at, now()) WHERE created_at IS NULL",
            "UPDATE escrows SET currency = :currency WHERE currency IS NULL",
            "UPDATE escrows SET refund_destination = sender_address WHERE refund_destination IS NULL",
            "ALTER TABLE escrows ALTER COLUMN created_at SET NOT NULL",
            "ALTER TABLE escrows ALTER COLUMN currency SET NOT NULL",
            "ALTER TABLE escrows ALTER COLUMN refund_destination SET NOT NULL",
        ]
        with self.engine.begin() as connection:
            for statement in statements:
                if ":currency" in statement:
                    connection.execute(text(statement), {"currency": self.config.currency})
                else:
                    connection.execute(text(statement))
            connection.execute(text(
                "DO $ DECLARE c RECORD; BEGIN "
                "FOR c IN SELECT conname FROM pg_constraint "
                "WHERE conrelid = 'escrows'::regclass AND contype = 'c' "
                "AND pg_get_constraintdef(oid) LIKE '%state%' LOOP "
                "EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT %I', c.conname); "
                "END LOOP; END $;"
            ))
            connection.execute(text(
                "ALTER TABLE escrows ADD CONSTRAINT ck_escrows_canonical_state "
                "CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'))"
            ))
            connection.execute(text(
                "INSERT INTO schema_version(version, checksum) VALUES (2, 'canonical-escrow-lifecycle-v2') "
                "ON CONFLICT (version) DO NOTHING"
            ))

    def _verify_canonical_schema(self) -> None:
        with self.engine.connect() as connection:
            assert_canonical_production_schema(connection)

    def create(self) -> GerchainRuntime:
        self.initialize()
        self._verify_canonical_schema()
        runtime = GerchainRuntime(
            escrow_id=self.config.escrow_id,
            amount=self.config.amount,
            currency=self.config.currency,
            witness_id=self.config.witness_id,
        )
        runtime.configure_canonical_ledger(self.session_factory)
        runtime.require_canonical_ledger_authority()
        return runtime


__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
