-- EA-35.14: align canonical ledger movement schema with ORM and deep reconciliation.
-- Additive migration only. Existing movement history is preserved.
-- Historical rows receive operation='TRANSFER'; escrow_id and integrity_hash remain NULL
-- until an audited backfill can prove their correct values. Deep reconciliation must
-- continue to flag unbackfilled historical rows rather than inventing evidence.

BEGIN;

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS operation VARCHAR(32);

UPDATE gerchain_ledger_movements
SET operation = 'TRANSFER'
WHERE operation IS NULL;

ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN operation SET DEFAULT 'TRANSFER';

ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN operation SET NOT NULL;

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS escrow_id VARCHAR(128);

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(128);

COMMIT;
