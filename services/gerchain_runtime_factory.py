from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from persistence.production_schema_guard import assert_canonical_production_schema
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
            ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
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
        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
        with self.engine.connect() as conn:
            apply_migrations(conn, migration_dir)

        # The migration runner owns historical schema versions. The ORM metadata
        # below supplies the canonical tables used by the current runtime.
        for base in (
            AtomicLedgerBase,
            EscrowBase,
            WitnessBase,
            OutboxBase,
            IdempotencyBase,
        ):
            base.metadata.create_all(self.engine)

        # Reconcile the legacy escrow table to the full canonical aggregate.
        with self.engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE escrows
                    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
                    ADD COLUMN IF NOT EXISTS currency TEXT,
                    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ
            """))
            conn.execute(text("""
                UPDATE escrows
                SET created_at = COALESCE(created_at, updated_at, now()),
                    currency = COALESCE(currency, :currency),
                    refund_destination = COALESCE(refund_destination, sender_address)
            """), {"currency": self.config.currency})
            conn.execute(text("ALTER TABLE escrows ALTER COLUMN created_at SET NOT NULL"))
            conn.execute(text("ALTER TABLE escrows ALTER COLUMN currency SET NOT NULL"))
            conn.execute(text("ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check"))
            conn.execute(text("""
                ALTER TABLE escrows
                ADD CONSTRAINT escrows_state_check
                CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'))
            """))

            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'gerchain_movement_operation_check'
                    ) THEN
                        ALTER TABLE gerchain_ledger_movements
                        ADD CONSTRAINT gerchain_movement_operation_check
                        CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT'))
                        NOT VALID;
                    END IF;
                END $$;
            """))
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'gerchain_movement_integrity_hash_check'
                    ) THEN
                        ALTER TABLE gerchain_ledger_movements
                        ADD CONSTRAINT gerchain_movement_integrity_hash_check
                        CHECK (integrity_hash IS NOT NULL AND length(integrity_hash) = 64)
                        NOT VALID;
                    END IF;
                END $$;
            """))
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'gerchain_movement_escrow_binding_check'
                    ) THEN
                        ALTER TABLE gerchain_ledger_movements
                        ADD CONSTRAINT gerchain_movement_escrow_binding_check
                        CHECK (
                            (operation = 'SETTLEMENT' AND escrow_id IS NULL)
                            OR
                            (operation IN ('FUND','RELEASE','REFUND','CANCEL') AND escrow_id IS NOT NULL)
                        )
                        NOT VALID;
                    END IF;
                END $$;
            """))

        with self.engine.connect() as conn:
            assert_canonical_production_schema(conn)

    def create(self) -> GerchainRuntime:
        self.initialize()
        runtime = GerchainRuntime(
            escrow_id=self.config.escrow_id,
            amount=self.config.amount,
            currency=self.config.currency,
            witness_id=self.config.witness_id,
        )
        runtime.configure_canonical_ledger(self.session_factory)
        runtime.require_canonical_ledger_authority()
        return runtime

    @classmethod
    def from_engine(
        cls,
        *,
        escrow_id: str,
        amount: int,
        currency: str,
        witness_id: str,
        engine: Engine,
        session_factory: Callable[[], Any] | None = None,
    ) -> GerchainRuntime:
        factory = cls(
            ProductionRuntimeConfig(
                database_url=str(engine.url),
                escrow_id=escrow_id,
                amount=amount,
                currency=currency,
                witness_id=witness_id,
            ),
            engine=engine,
        )
        if session_factory is not None:
            factory.session_factory = session_factory
        return factory.create()

    build = create


__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
