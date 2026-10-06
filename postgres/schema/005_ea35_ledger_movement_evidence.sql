-- EA-35 production schema alignment
-- Align existing canonical Ledger movement tables with the runtime evidence contract.
-- Structural only; no value movement.

BEGIN;

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS operation VARCHAR(32) NOT NULL DEFAULT 'TRANSFER';

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS escrow_id VARCHAR(128);

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(128);

COMMIT;
