"""Canonical PostgreSQL schema reconciliation for production GerChain.

This is an additive/idempotent bootstrap for the current canonical persistence
models. It upgrades the legacy escrow state constraint without moving value.
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase


def initialize_canonical_production_schema(engine: Engine) -> None:
    """Create canonical tables and reconcile the legacy escrow schema.

    No value movement is performed. Existing escrow rows are preserved.
    """
    for base in (
        AtomicLedgerBase,
        EscrowBase,
        WitnessBase,
        OutboxBase,
        IdempotencyBase,
    ):
        base.metadata.create_all(engine)

    if engine.dialect.name != "postgresql":
        raise ValueError("canonical production schema requires PostgreSQL")

    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT"
        ))
        connection.execute(text(
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency VARCHAR(16)"
        ))
        connection.execute(text(
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0"
        ))
        connection.execute(text(
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ"
        ))
        connection.execute(text(
            "ALTER TABLE escrows ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ"
        ))
        connection.execute(text(
            "UPDATE escrows SET created_at = COALESCE(created_at, updated_at, now()) "
            "WHERE created_at IS NULL"
        ))
        connection.execute(text(
            "UPDATE escrows SET updated_at = COALESCE(updated_at, created_at, now()) "
            "WHERE updated_at IS NULL"
        ))
        connection.execute(text(
            "ALTER TABLE escrows ALTER COLUMN created_at SET NOT NULL"
        ))
        connection.execute(text(
            "ALTER TABLE escrows ALTER COLUMN updated_at SET NOT NULL"
        ))

        # Remove only legacy CHECK constraints that constrain escrow.state.
        connection.execute(text(
            """
            DO $$
            DECLARE constraint_row RECORD;
            BEGIN
              FOR constraint_row IN
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'escrows'::regclass
                  AND contype = 'c'
                  AND pg_get_constraintdef(oid) ILIKE '%state%'
              LOOP
                EXECUTE format(
                  'ALTER TABLE escrows DROP CONSTRAINT %I',
                  constraint_row.conname
                );
              END LOOP;
            END $$;
            """
        ))
        connection.execute(text(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conrelid = 'escrows'::regclass
                  AND conname = 'ck_escrows_canonical_state'
              ) THEN
                ALTER TABLE escrows
                ADD CONSTRAINT ck_escrows_canonical_state
                CHECK (state IN (
                  'CREATED', 'FUNDED', 'LOCKED',
                  'RELEASED', 'REFUNDED', 'CANCELLED'
                ));
              END IF;
            END $$;
            """
        ))
        connection.execute(text(
            "ALTER TABLE escrows ALTER COLUMN state SET DEFAULT 'CREATED'"
        ))
