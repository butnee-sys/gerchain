-- GerChain canonical production persistence migration
-- EA-35.14
-- Purpose: align PostgreSQL schema with the canonical Ledger/Escrow/Witness/
-- Outbox/Idempotency models. This migration is additive except for the
-- legacy escrow state CHECK, which is replaced with the frozen lifecycle.

BEGIN;

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance BIGINT NOT NULL,
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

CREATE TABLE IF NOT EXISTS escrows (
    id VARCHAR PRIMARY KEY,
    sender_address VARCHAR NOT NULL,
    receiver_address VARCHAR NOT NULL,
    amount NUMERIC(38,8) NOT NULL CHECK (amount >= 0),
    state VARCHAR(32) NOT NULL,
    condition_desc VARCHAR,
    refund_destination VARCHAR,
    currency VARCHAR(16),
    version BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination VARCHAR;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency VARCHAR(16);
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;

UPDATE escrows
SET created_at = COALESCE(created_at, updated_at)
WHERE created_at IS NULL;

ALTER TABLE escrows ALTER COLUMN created_at SET NOT NULL;

DO $$
DECLARE c RECORD;
BEGIN
    FOR c IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND contype = 'c'
          AND pg_get_constraintdef(oid) ILIKE '%state%'
    LOOP
        EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT %I', c.conname);
    END LOOP;
END $$;

ALTER TABLE escrows
    ADD CONSTRAINT ck_escrows_state_canonical
    CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));

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
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_claim
    ON gerchain_outbox_events (state, lease_until, id);

CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    fingerprint VARCHAR(64) NOT NULL,
    result_json TEXT,
    state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_version (
    version BIGINT PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO schema_version(version, checksum)
VALUES (2, 'EA-35.14-canonical-production-persistence')
ON CONFLICT (version) DO NOTHING;

COMMIT;
