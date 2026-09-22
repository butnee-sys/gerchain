-- Canonical escrow lifecycle extension.
-- Migration 001 creates the legacy escrow table. This migration extends it
-- without inventing currency or other financial metadata.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

UPDATE escrows
SET refund_destination = sender_address
WHERE refund_destination IS NULL;

ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check;

ALTER TABLE escrows ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));
