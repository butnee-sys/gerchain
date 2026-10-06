-- EA-35 canonical movement evidence hardening
-- Adds fields required by the authoritative LedgerMovementModel and deep value-truth reconciliation.
BEGIN;

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS operation VARCHAR(32) NOT NULL DEFAULT 'TRANSFER';

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS escrow_id VARCHAR(128);

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(128);

COMMIT;
