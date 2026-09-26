-- GerChain canonical production persistence.
-- EA-35.14: canonical Ledger/Escrow/Evidence schema.

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
    account_id VARCHAR(128) PRIMARY KEY,
    currency VARCHAR(16) NOT NULL,
    balance INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gerchain_ledger_movements (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    source VARCHAR(128) NOT NULL,
    destination VARCHAR(128) NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    currency VARCHAR(16) NOT NULL,
    operation VARCHAR(32) NOT NULL DEFAULT 'TRANSFER',
    escrow_id VARCHAR(128),
    integrity_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency VARCHAR(16);
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
UPDATE escrows SET created_at = updated_at WHERE created_at IS NULL;

DO $$
DECLARE c RECORD;
BEGIN
  FOR c IN
    SELECT conname FROM pg_constraint
    WHERE conrelid = 'escrows'::regclass AND contype = 'c'
      AND pg_get_constraintdef(oid) LIKE '%state%'
  LOOP
    EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT %I', c.conname);
  END LOOP;
END $$;

ALTER TABLE escrows
  ADD CONSTRAINT escrows_state_canonical_check
  CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));

CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    escrow_id VARCHAR(255) NOT NULL,
    amount INTEGER NOT NULL,
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
    attempts INTEGER NOT NULL DEFAULT 0,
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

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'gerchain_movement_operation_check') THEN
    ALTER TABLE gerchain_ledger_movements ADD CONSTRAINT gerchain_movement_operation_check
      CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT','TRANSFER'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'gerchain_movement_integrity_hash_check') THEN
    ALTER TABLE gerchain_ledger_movements ADD CONSTRAINT gerchain_movement_integrity_hash_check
      CHECK (integrity_hash IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'gerchain_movement_escrow_binding_check') THEN
    ALTER TABLE gerchain_ledger_movements ADD CONSTRAINT gerchain_movement_escrow_binding_check
      CHECK ((operation = 'SETTLEMENT' AND escrow_id IS NULL)
          OR (operation <> 'SETTLEMENT' AND escrow_id IS NOT NULL AND length(escrow_id) > 0));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow ON gerchain_ledger_movements (escrow_id);
CREATE INDEX IF NOT EXISTS ix_gerchain_witnesses_escrow ON gerchain_transaction_witnesses (escrow_id);
CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_aggregate ON gerchain_outbox_events (aggregate_id);
