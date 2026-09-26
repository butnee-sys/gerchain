-- Canonical production persistence for EAI value flow.
-- Extends the legacy concurrency schema without introducing a second authority.

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE escrows ALTER COLUMN condition_desc DROP NOT NULL;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency VARCHAR(16);
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Preserve the pre-canonical sender as the historical refund destination.
UPDATE escrows
SET refund_destination = COALESCE(refund_destination, sender_address),
    created_at = COALESCE(created_at, updated_at);

ALTER TABLE escrows ALTER COLUMN currency SET NOT NULL;

ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check;
ALTER TABLE escrows DROP CONSTRAINT IF EXISTS gerchain_escrow_state_check;
ALTER TABLE escrows ADD CONSTRAINT gerchain_escrow_state_check
    CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));

CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    escrow_id VARCHAR(255) NOT NULL,
    amount INTEGER NOT NULL CHECK (amount >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    fingerprint VARCHAR(64) NOT NULL,
    result_json TEXT,
    state VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_operation_check;
ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT'));
ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_integrity_hash_check;
ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (length(integrity_hash) = 64);
ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;
ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        (operation = 'SETTLEMENT' AND escrow_id IS NULL)
        OR (operation IN ('FUND','RELEASE','REFUND','CANCEL') AND escrow_id IS NOT NULL)
         
    );

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow
    ON gerchain_ledger_movements (escrow_id);
CREATE INDEX IF NOT EXISTS ix_gerchain_witness_escrow
    ON gerchain_transaction_witnesses (escrow_id);
CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_aggregate
    ON gerchain_outbox_events (aggregate_id);


