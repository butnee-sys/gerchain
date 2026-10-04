-- EA-22 canonical durable escrow lifecycle
-- Expands the existing escrow aggregate in place. No value movement occurs.
-- This migration is structural only and must be followed by reconciliation.

BEGIN;

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT;

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS currency TEXT;

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Existing rows are CREATED/LOCKED/RELEASED. Add the remaining canonical states
-- without replacing the existing aggregate/table.
ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

CREATE INDEX IF NOT EXISTS ix_escrows_state ON escrows (state);
CREATE INDEX IF NOT EXISTS ix_escrows_updated_at ON escrows (updated_at);

COMMIT;
