-- GerChain canonical production persistence migration
-- EA-35.14
-- This migration establishes the persistence contract used by the
-- Canonical Ledger + Escrow Aggregate + Witness + Idempotency + Outbox.
-- It is intentionally additive/idempotent. Legacy tables are NOT silently
-- deleted; their production authority must be frozen separately.

CREATE TABLE IF NOT EXISTS schema_version (
    version BIGINT PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Canonical Escrow aggregate. Existing legacy escrows are upgraded in place;
-- a fresh production database gets the canonical table directly.
CREATE TABLE IF NOT EXISTS escrows (
    id VARCHAR(255) PRIMARY KEY,
    sender_address VARCHAR(255) NOT NULL,
    receiver_address VARCHAR(255) NOT NULL,
    amount NUMERIC(38, 8) NOT NULL CHECK (amount >= 0),
    state VARCHAR(32) NOT NULL,
    condition_desc TEXT,
    refund_destination TEXT,
    currency VARCHAR(16),
    version BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT escrows_state_check CHECK (
        state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED')
    )
);

ALTER TABLE IF EXISTS escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;

UPDATE escrows
SET created_at = COALESCE(created_at, updated_at, now())
WHERE created_at IS NULL;

ALTER TABLE IF EXISTS escrows
    ALTER COLUMN created_at SET NOT NULL;

ALTER TABLE IF EXISTS escrows
    DROP CONSTRAINT IF EXISTS escrows_state_check;

ALTER TABLE IF EXISTS escrows DROP CONSTRAINT IF EXISTS escrows_state_check;
ALTER TABLE IF EXISTS escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

ALTER TABLE IF EXISTS gerchain_ledger_accounts
    DROP CONSTRAINT IF EXISTS gerchain_ledger_account_balance_check;
ALTER TABLE IF EXISTS gerchain_ledger_accounts
    ADD CONSTRAINT gerchain_ledger_account_balance_check CHECK (balance >= 0);

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance BIGINT NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL
);

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
    created_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE IF EXISTS gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_amount_check;
ALTER TABLE IF EXISTS gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_amount_check CHECK (amount > 0);
ALTER TABLE IF EXISTS gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_operation_check;
ALTER TABLE IF EXISTS gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT'));
ALTER TABLE IF EXISTS gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_integrity_hash_check;
ALTER TABLE IF EXISTS gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (length(integrity_hash) = 64);
ALTER TABLE IF EXISTS gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;
ALTER TABLE IF EXISTS gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        (operation = 'SETTLEMENT' AND escrow_id IS NULL)
        OR (operation IN ('FUND','RELEASE','REFUND','CANCEL') AND escrow_id IS NOT NULL)
    );

CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    escrow_id VARCHAR(255) NOT NULL,
    amount BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE IF EXISTS gerchain_transaction_witnesses
    DROP CONSTRAINT IF EXISTS gerchain_witness_amount_check;
ALTER TABLE IF EXISTS gerchain_transaction_witnesses
    ADD CONSTRAINT gerchain_witness_amount_check CHECK (amount >= 0);

CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    fingerprint VARCHAR(64) NOT NULL,
    result_json TEXT,
    state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE IF EXISTS gerchain_idempotency_records
    DROP CONSTRAINT IF EXISTS gerchain_idempotency_state_check;
ALTER TABLE IF EXISTS gerchain_idempotency_records
    ADD CONSTRAINT gerchain_idempotency_state_check
    CHECK (state IN ('PROCESSING','COMPLETED'));

CREATE TABLE IF NOT EXISTS gerchain_outbox_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type VARCHAR(128) NOT NULL,
    aggregate_id VARCHAR(255) NOT NULL,
    payload_json TEXT NOT NULL,
    state VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    lease_until TIMESTAMPTZ,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

