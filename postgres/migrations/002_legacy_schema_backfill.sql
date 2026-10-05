-- Backfill canonical escrow columns for legacy PostgreSQL escrows.
-- Safe for fresh databases and existing legacy rows.

ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency TEXT;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE gerchain_ledger_movements ADD COLUMN IF NOT EXISTS operation VARCHAR(32);
ALTER TABLE gerchain_ledger_movements ADD COLUMN IF NOT EXISTS escrow_id VARCHAR(128);
ALTER TABLE gerchain_ledger_movements ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(128);

UPDATE gerchain_ledger_movements
SET operation = COALESCE(operation, 'TRANSFER')
WHERE operation IS NULL;

ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN operation SET NOT NULL;
