from __future__ import annotations

from sqlalchemy import text


CANONICAL_SCHEMA_SQL = (
    """
    ALTER TABLE escrows
        ADD COLUMN IF NOT EXISTS refund_destination TEXT,
        ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
        ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
        id SERIAL PRIMARY KEY,
        transaction_id VARCHAR(128) NOT NULL UNIQUE,
        source VARCHAR(128) NOT NULL,
        destination VARCHAR(128) NOT NULL,
        amount BIGINT NOT NULL,
        currency VARCHAR(16) NOT NULL,
        operation VARCHAR(32) NOT NULL DEFAULT 'TRANSFER',
        escrow_id VARCHAR(128),
        integrity_hash VARCHAR(128),
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
        id SERIAL PRIMARY KEY,
        transaction_id VARCHAR(128) NOT NULL UNIQUE,
        event_type VARCHAR(64) NOT NULL,
        escrow_id VARCHAR(255) NOT NULL,
        amount BIGINT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS gerchain_outbox_events (
        id SERIAL PRIMARY KEY,
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
        id SERIAL PRIMARY KEY,
        key VARCHAR(255) NOT NULL UNIQUE,
        fingerprint VARCHAR(64) NOT NULL,
        result_json TEXT,
        state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
)


def initialize_canonical_postgres_schema(engine) -> None:
    """Apply the minimal additive schema required by the canonical runtime."""
    with engine.begin() as connection:
        for statement in CANONICAL_SCHEMA_SQL:
            connection.execute(text(statement))


__all__ = ["initialize_canonical_postgres_schema", "CANONICAL_SCHEMA_SQL"]
