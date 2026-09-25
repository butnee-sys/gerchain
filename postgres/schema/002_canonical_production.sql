-- Canonical production persistence for EAI / GerChain value truth.
-- Version 2 upgrades the legacy escrow schema and creates the single
-- authoritative Ledger + Witness + transactional Outbox + Idempotency stores.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

UPDATE escrows
SET currency = COALESCE(currency, 'MNT'),
    created_at = COALESCE(created_at, updated_at, now())
WHERE currency IS NULL OR created_at IS NULL;

DO $$
DECLARE c RECORD;
BEGIN
    FOR c IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND contype = 'c'
          AND pg_get_constraintdef(oid) LIKE '%state%'
    LOOP
        EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT %I', c.conname);
    END LOOP;
END $$;

ALTER TABLE escrows
    DROP CONSTRAINT IF EXISTS escrows_state_check;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance INTEGER NOT NULL CHECK (balance >= 0),
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS gerchain_ledger_movements (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    source VARCHAR(128) NOT NULL,
    destination VARCHAR(128) NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
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
    amount INTEGER NOT NULL,
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
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_claim
    ON gerchain_outbox_events (state, lease_until, id);

CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    fingerprint VARCHAR(64) NOT NULL,
    result_json TEXT,
    state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow
    ON gerchain_ledger_movements (escrow_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_witness_escrow
    ON gerchain_transaction_witnesses (escrow_id);
