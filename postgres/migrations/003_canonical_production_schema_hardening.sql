-- Canonical production schema hardening.
-- Version 3: complete the durable value-truth contract without mutating
-- immutable migration versions 1 or 2.

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance BIGINT NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS operation VARCHAR(32);
ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS escrow_id VARCHAR(128);
ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(128);
ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

UPDATE gerchain_ledger_movements
SET operation = 'TRANSFER'
WHERE operation IS NULL;

ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN operation SET DEFAULT 'TRANSFER';
ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN operation SET NOT NULL;
ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN integrity_hash SET NOT NULL;

ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency VARCHAR(16);
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

DO $$
DECLARE
    c RECORD;
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
    ADD CONSTRAINT ck_escrows_canonical_state
    CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));
ALTER TABLE escrows
    ALTER COLUMN refund_destination SET NOT NULL;
ALTER TABLE escrows
    ALTER COLUMN currency SET NOT NULL;

CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    escrow_id VARCHAR(255) NOT NULL,
    amount BIGINT NOT NULL,
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

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'gerchain_movement_amount_check'
          AND conrelid = 'gerchain_ledger_movements'::regclass
    ) THEN
        ALTER TABLE gerchain_ledger_movements
            ADD CONSTRAINT gerchain_movement_amount_check CHECK (amount > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'gerchain_movement_operation_check'
          AND conrelid = 'gerchain_ledger_movements'::regclass
    ) THEN
        ALTER TABLE gerchain_ledger_movements
            ADD CONSTRAINT gerchain_movement_operation_check
            CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT','TRANSFER'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'gerchain_movement_integrity_hash_check'
          AND conrelid = 'gerchain_ledger_movements'::regclass
    ) THEN
        ALTER TABLE gerchain_ledger_movements
            ADD CONSTRAINT gerchain_movement_integrity_hash_check
            CHECK (integrity_hash IS NOT NULL AND length(integrity_hash) = 64);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'gerchain_movement_escrow_binding_check'
          AND conrelid = 'gerchain_ledger_movements'::regclass
    ) THEN
        ALTER TABLE gerchain_ledger_movements
            ADD CONSTRAINT gerchain_movement_escrow_binding_check
            CHECK (
                (operation = 'SETTLEMENT' AND escrow_id IS NULL)
                OR
                (operation IN ('FUND','RELEASE','REFUND','CANCEL') AND escrow_id IS NOT NULL)
                OR
                (operation = 'TRANSFER')
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'gerchain_witness_amount_check'
          AND conrelid = 'gerchain_transaction_witnesses'::regclass
    ) THEN
        ALTER TABLE gerchain_transaction_witnesses
            ADD CONSTRAINT gerchain_witness_amount_check CHECK (amount >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'gerchain_idempotency_state_check'
          AND conrelid = 'gerchain_idempotency_records'::regclass
    ) THEN
        ALTER TABLE gerchain_idempotency_records
            ADD CONSTRAINT gerchain_idempotency_state_check
            CHECK (state IN ('PROCESSING','COMPLETED'));
    END IF;
END $$;
