-- EA-35 canonical value-truth persistence hardening.
-- Adds evidence-binding columns required by the production runtime.
BEGIN;

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS operation VARCHAR(32) NOT NULL DEFAULT 'TRANSFER';
ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS escrow_id VARCHAR(128);
ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(128);

COMMIT;
