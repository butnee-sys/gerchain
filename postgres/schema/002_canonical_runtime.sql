-- Canonical GerChain production persistence migration.
-- Extends the legacy escrow schema without introducing a second authority.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;

UPDATE escrows
SET created_at = COALESCE(created_at, updated_at, now())
WHERE created_at IS NULL;

ALTER TABLE escrows
    ALTER COLUMN created_at SET NOT NULL;

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    SELECT con.conname
      INTO constraint_name
      FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
     WHERE rel.relname = 'escrows'
       AND nsp.nspname = current_schema()
       AND con.contype = 'c'
       AND pg_get_constraintdef(con.oid) ILIKE '%state%';

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT %I', constraint_name);
    END IF;
END $$;

ALTER TABLE escrows
    ADD CONSTRAINT ck_escrows_state_canonical
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gerchain_ledger_movements (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    source VARCHAR(128) NOT NULL,
    destination VARCHAR(128) NOT NULL,
    amount INTEGER NOT NULL,
    currency VARCHAR(16) NOT NULL,
    operation VARCHAR(32) NOT NULL DEFAULT 'TRANSFER',
    escrow_id VARCHAR(128),
    integrity_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    escrow_id VARCHAR(255) NOT NULL,
    amount INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    fingerprint VARCHAR(64) NOT NULL,
    result_json TEXT,
    state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
