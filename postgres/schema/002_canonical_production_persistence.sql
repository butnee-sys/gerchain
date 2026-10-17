-- GerChain canonical production persistence
-- EA-35.13
-- Idempotent migration. Existing rows with missing canonical escrow fields
-- intentionally fail the migration instead of being silently defaulted.

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance BIGINT NOT NULL CHECK (balance >= 0),
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS gerchain_ledger_movements (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    source VARCHAR(128) NOT NULL,
    destination VARCHAR(128) NOT NULL,
    amount BIGINT NOT NULL CHECK (amount > 0),
    currency VARCHAR(16) NOT NULL,
    operation VARCHAR(32) NOT NULL,
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

CREATE TABLE IF NOT EXISTS gerchain_outbox_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type VARCHAR(128) NOT NULL,
    aggregate_id VARCHAR(255) NOT NULL,
    payload_json TEXT NOT NULL,
    state VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    lease_until TIMESTAMPTZ,
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
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

ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency VARCHAR(16);
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM escrows WHERE currency IS NULL) THEN
        RAISE EXCEPTION 'EA-35.13 migration blocked: existing escrows require explicit currency backfill';
    END IF;
    IF EXISTS (SELECT 1 FROM escrows WHERE refund_destination IS NULL) THEN
        RAISE EXCEPTION 'EA-35.13 migration blocked: existing escrows require explicit refund_destination backfill';
    END IF;
END $$;

ALTER TABLE escrows ALTER COLUMN currency SET NOT NULL;
ALTER TABLE escrows ALTER COLUMN refund_destination SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow
    ON gerchain_ledger_movements (escrow_id);
CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_claim
    ON gerchain_outbox_events (state, lease_until, id);
CREATE INDEX IF NOT EXISTS ix_gerchain_idempotency_state
    ON gerchain_idempotency_records (state, updated_at);

INSERT INTO schema_version(version, checksum)
SELECT 2, 'EA-35.13-canonical-production-persistence'
WHERE NOT EXISTS (SELECT 1 FROM schema_version WHERE version = 2);
