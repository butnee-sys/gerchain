"""Canonical PostgreSQL production schema bootstrap/migration boundary.

This is deliberately limited to additive/compatible persistence preparation.
It is not a general migration framework; release environments should still
run reviewed schema migrations explicitly.
"""
from __future__ import annotations

from sqlalchemy import text


_ESCROWS = """
CREATE TABLE IF NOT EXISTS escrows (
    id TEXT PRIMARY KEY,
    sender_address TEXT NOT NULL,
    receiver_address TEXT NOT NULL,
    amount NUMERIC(38, 8) NOT NULL CHECK (amount >= 0),
    state TEXT NOT NULL CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED')),
    condition_desc TEXT,
    refund_destination TEXT,
    currency VARCHAR(16),
    version BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

_TABLES = [
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
]


def initialize_production_schema(engine) -> None:
    """Prepare the canonical PostgreSQL persistence schema.

    Existing legacy escrow rows are preserved. Missing canonical columns are
    added, and the escrow state constraint is upgraded to the frozen lifecycle.
    """
    if engine.dialect.name != "postgresql":
        raise ValueError("canonical production schema requires PostgreSQL")

    with engine.begin() as connection:
        connection.execute(text(_ESCROWS))
        connection.execute(text("ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT"))
        connection.execute(text("ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency VARCHAR(16)"))
        connection.execute(text("ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0"))
        connection.execute(text("ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ"))
        connection.execute(text("UPDATE escrows SET created_at = updated_at WHERE created_at IS NULL"))
        connection.execute(text("ALTER TABLE escrows ALTER COLUMN created_at SET NOT NULL"))
        connection.execute(text("ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check"))
        connection.execute(text(
            "ALTER TABLE escrows ADD CONSTRAINT escrows_state_check "
            "CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'))"
        ))
        for statement in _TABLES:
            connection.execute(text(statement))
