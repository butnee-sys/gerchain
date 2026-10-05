-- Backfill canonical escrow columns for legacy PostgreSQL escrows.
-- Safe for fresh databases and existing legacy rows.

ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS currency TEXT;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

