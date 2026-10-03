-- GerChain canonical production persistence migration
-- EA-35.14
-- This migration establishes the persistence contract used by the
-- Canonical Ledger + Escrow Aggregate + Witness + Idempotency + Outbox.
-- It is intentionally additive/idempotent. Legacy tables are NOT silently
-- deleted; their production authority must be frozen separately.

BEGIN;

CREATE TABLE IF NOT EXISTS schema_version (
    version BIGINT PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Canonical Escrow aggregate. Existing escrows from 001_concurrency are
-- upgraded in place when present.
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

ALTER TABLE IF EXISTS escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

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

CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    escrow_id VARCHAR(255) NOT NULL,
    amount BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    fingerprint VARCHAR(64) NOT NULL,
    result_json TEXT,
    state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

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

INSERT INTO schema_version(version, checksum)
VALUES (2, 'EA-35.14-canonical-production-persistence')
ON CONFLICT (version) DO NOTHING;

COMMIT;
