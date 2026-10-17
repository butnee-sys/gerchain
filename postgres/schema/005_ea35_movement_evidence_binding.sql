-- EA-35 canonical movement evidence binding
-- Structural only; no value movement.
BEGIN;

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS operation VARCHAR(32);

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS escrow_id VARCHAR(128);

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(128);

UPDATE gerchain_ledger_movements
SET operation = 'TRANSFER'
WHERE operation IS NULL;

ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN operation SET NOT NULL;

COMMIT;
