-- Canonical production schema completion
-- Upgrades legacy PostgreSQL escrow schema without rewriting migration history.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE escrows
    ALTER COLUMN state DROP DEFAULT;

ALTER TABLE escrows
    DROP CONSTRAINT IF EXISTS escrows_state_check;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance BIGINT NOT NULL DEFAULT 0 CHECK (balance >= 0),
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS gerchain_ledger_movements (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL,
    source VARCHAR(128) NOT NULL,
    destination VARCHAR(128) NOT NULL,
    amount BIGINT NOT NULL CHECK (amount > 0),
    currency VARCHAR(16) NOT NULL,
    operation VARCHAR(32) NOT NULL,
    escrow_id VARCHAR(128),
    integrity_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_gerchain_ledger_transaction UNIQUE (transaction_id),
    CONSTRAINT gerchain_movement_operation_check
        CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT','TRANSFER')),
    CONSTRAINT gerchain_movement_integrity_hash_check
        CHECK (integrity_hash IS NOT NULL AND length(integrity_hash) = 64),
    CONSTRAINT gerchain_movement_escrow_binding_check
        CHECK (
            (operation = 'SETTLEMENT' AND escrow_id IS NULL)
            OR
            (operation IN ('FUND','RELEASE','REFUND','CANCEL') AND escrow_id IS NOT NULL AND length(escrow_id) > 0)
            OR
            (operation = 'TRANSFER' AND escrow_id IS NULL)
        )
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
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
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

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_transaction
    ON gerchain_ledger_movements (transaction_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_pending
    ON gerchain_outbox_events (state, id);

CREATE INDEX IF NOT EXISTS ix_gerchain_idempotency_key
    ON gerchain_idempotency_records (key);
