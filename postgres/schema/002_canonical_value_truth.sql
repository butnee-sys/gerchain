-- Canonical production value-truth schema upgrade.
-- Extends the legacy escrow table and creates the single canonical
-- Ledger + Witness + Outbox + Idempotency persistence boundary.

ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check;

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency TEXT,
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

UPDATE escrows
SET refund_destination = COALESCE(refund_destination, sender_address),
    currency = COALESCE(currency, 'MNT')
WHERE refund_destination IS NULL OR currency IS NULL;

ALTER TABLE escrows
    ALTER COLUMN refund_destination SET NOT NULL,
    ALTER COLUMN currency SET NOT NULL;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance BIGINT NOT NULL,
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS gerchain_ledger_movements (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    source VARCHAR(128) NOT NULL,
    destination VARCHAR(128) NOT NULL,
    amount BIGINT NOT NULL,
    currency VARCHAR(16) NOT NULL,
    operation VARCHAR(32) NOT NULL,
    escrow_id VARCHAR(128),
    integrity_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    escrow_id VARCHAR(255) NOT NULL,
    amount BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS gerchain_outbox_events (
    id BIGSERIAL PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    fingerprint VARCHAR(64) NOT NULL,
    result_json TEXT,
    state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
