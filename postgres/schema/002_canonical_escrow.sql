-- Canonical durable escrow aggregate alignment.
-- Migrates the legacy escrow table to the production lifecycle contract.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

UPDATE escrows
SET created_at = COALESCE(created_at, updated_at, now())
WHERE created_at IS NULL;

ALTER TABLE escrows
    DROP CONSTRAINT IF EXISTS escrows_state_check;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN (
        'CREATED',
        'FUNDED',
        'LOCKED',
        'RELEASED',
        'REFUNDED',
        'CANCELLED'
    ));
