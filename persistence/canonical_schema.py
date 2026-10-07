"""Idempotent PostgreSQL schema migration for canonical production value flow."""
from __future__ import annotations

from sqlalchemy import text


_MIGRATION_VERSION = 2

_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version BIGINT PRIMARY KEY,
        checksum TEXT NOT NULL,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    ALTER TABLE escrows
        ADD COLUMN IF NOT EXISTS refund_destination TEXT,
        ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
        ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    """,
    """
    DO $$
    DECLARE c RECORD;
    BEGIN
      FOR c IN
        SELECT conname FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass AND contype = 'c'
      LOOP
        EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT IF EXISTS %I', c.conname);
      END LOOP;
      ALTER TABLE escrows
        ADD CONSTRAINT escrows_amount_nonnegative CHECK (amount >= 0),
        ADD CONSTRAINT escrows_state_valid CHECK (
          state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED')
        );
    END $$;
    """,
    """
    CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
        account_id VARCHAR(128) PRIMARY KEY,
        currency VARCHAR(16) NOT NULL,
        balance BIGINT NOT NULL DEFAULT 0,
        version INTEGER NOT NULL DEFAULT 0,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS gerchain_ledger_movements (
        id BIGSERIAL PRIMARY KEY,
        transaction_id VARCHAR(128) NOT NULL UNIQUE,
        source VARCHAR(128) NOT NULL,
        destination VARCHAR(128) NOT NULL,
        amount BIGINT NOT NULL CHECK (amount > 0),
        currency VARCHAR(16) NOT NULL,
        operation VARCHAR(32) NOT NULL,
        escrow_id VARCHAR(128),
        integrity_hash VARCHAR(128),
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
        id BIGSERIAL PRIMARY KEY,
        transaction_id VARCHAR(128) NOT NULL UNIQUE,
        event_type VARCHAR(64) NOT NULL,
        escrow_id VARCHAR(255) NOT NULL,
        amount BIGINT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS gerchain_outbox_events (
        id BIGSERIAL PRIMARY KEY,
        event_id VARCHAR(255) NOT NULL UNIQUE,
        event_type VARCHAR(128) NOT NULL,
        aggregate_id VARCHAR(255) NOT NULL,
        payload_json TEXT NOT NULL,
        state VARCHAR(32) NOT NULL DEFAULT 'PENDING',
        lease_until TIMESTAMPTZ,
        attempts INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (
        id BIGSERIAL PRIMARY KEY,
        key VARCHAR(255) NOT NULL UNIQUE,
        fingerprint VARCHAR(64) NOT NULL,
        result_json TEXT,
        state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
)


def initialize_canonical_schema(engine) -> None:
    """Apply the canonical PostgreSQL schema as one idempotent migration.

    This is intentionally PostgreSQL-only and does not silently migrate legacy
    value stores into canonical authority.
    """
    if engine.dialect.name != "postgresql":
        raise ValueError("canonical production schema requires PostgreSQL")
    with engine.begin() as connection:
        for statement in _STATEMENTS:
            connection.execute(text(statement))
        connection.execute(
            text(
                "INSERT INTO schema_version(version, checksum) "
                "VALUES (:version, :checksum) "
                "ON CONFLICT (version) DO NOTHING"
            ),
            {"version": _MIGRATION_VERSION, "checksum": "canonical-value-flow-v2"},
        )


__all__ = ["initialize_canonical_schema"]
