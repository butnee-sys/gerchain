-- Canonical GerChain production persistence hardening.
-- Version 006: enforce canonical escrow metadata required by the runtime.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;

UPDATE escrows
SET refund_destination = COALESCE(refund_destination, sender_address),
    currency = COALESCE(currency, 'MNT'),
    created_at = COALESCE(created_at, updated_at, now())
WHERE refund_destination IS NULL OR currency IS NULL OR created_at IS NULL;

ALTER TABLE escrows
    ALTER COLUMN currency SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL;

ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check;
ALTER TABLE escrows DROP CONSTRAINT IF EXISTS gerchain_escrow_state_check;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));
