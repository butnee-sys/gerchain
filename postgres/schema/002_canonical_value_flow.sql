-- GerChain canonical production persistence
-- Evolves legacy escrow storage and creates the single canonical value-flow evidence stores.

DO $$
DECLARE c RECORD;
BEGIN
  IF to_regclass('public.escrows') IS NOT NULL THEN
    FOR c IN
      SELECT conname FROM pg_constraint
      WHERE conrelid = 'public.escrows'::regclass AND contype = 'c'
    LOOP
      EXECUTE format('ALTER TABLE public.escrows DROP CONSTRAINT %I', c.conname);
    END LOOP;
    ALTER TABLE public.escrows
      ADD COLUMN IF NOT EXISTS refund_destination TEXT,
      ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
      ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
      ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
    ALTER TABLE public.escrows
      ALTER COLUMN amount TYPE NUMERIC(38,8) USING amount::NUMERIC(38,8),
      ALTER COLUMN state SET DEFAULT 'CREATED';
    ALTER TABLE public.escrows
      ADD CONSTRAINT ck_escrows_state_canonical
      CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));
  ELSE
    CREATE TABLE public.escrows (
      id TEXT PRIMARY KEY,
      sender_address TEXT NOT NULL,
      receiver_address TEXT NOT NULL,
      amount NUMERIC(38,8) NOT NULL CHECK (amount >= 0),
      state TEXT NOT NULL DEFAULT 'CREATED' CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED')),
      condition_desc TEXT,
      refund_destination TEXT,
      currency VARCHAR(16),
      version BIGINT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS gerchain_ledger_accounts (
  account_id VARCHAR(128) PRIMARY KEY,
  currency VARCHAR(16) NOT NULL,
  balance BIGINT NOT NULL DEFAULT 0,
  version INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gerchain_ledger_movements (
  id BIGSERIAL PRIMARY KEY,
  transaction_id VARCHAR(128) NOT NULL UNIQUE,
  source VARCHAR(128) NOT NULL,
  destination VARCHAR(128) NOT NULL,
  amount BIGINT NOT NULL CHECK (amount > 0),
  currency VARCHAR(16) NOT NULL,
  operation VARCHAR(32) NOT NULL,
  escrow_id VARCHAR(128),
  integrity_hash VARCHAR(128),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gerchain_transaction_witnesses (
  id BIGSERIAL PRIMARY KEY,
  transaction_id VARCHAR(128) NOT NULL UNIQUE,
  event_type VARCHAR(64) NOT NULL,
  escrow_id VARCHAR(255) NOT NULL,
  amount BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
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

CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_claim
  ON gerchain_outbox_events (state, id);
CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movement_escrow
  ON gerchain_ledger_movements (escrow_id, created_at);
CREATE INDEX IF NOT EXISTS ix_gerchain_witness_escrow
  ON gerchain_transaction_witnesses (escrow_id, created_at);
