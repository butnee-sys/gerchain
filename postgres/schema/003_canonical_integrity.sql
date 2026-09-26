-- Canonical production integrity hardening.
-- Version 003 is additive; migration 001/002 checksums remain immutable.

UPDATE escrows SET currency = 'UNKNOWN' WHERE currency IS NULL;
ALTER TABLE escrows ALTER COLUMN currency SET NOT NULL;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT','TRANSFER'));

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (operation = 'TRANSFER' OR escrow_id IS NOT NULL);

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (operation = 'TRANSFER' OR integrity_hash IS NOT NULL);
