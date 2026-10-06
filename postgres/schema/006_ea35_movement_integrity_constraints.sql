-- EA-35 movement integrity and escrow binding constraints
-- Structural only; no value movement.
BEGIN;

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_operation_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('TRANSFER', 'FUND', 'RELEASE', 'REFUND', 'CANCEL', 'SETTLEMENT'));

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_integrity_hash_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (
        operation = 'TRANSFER'
        OR integrity_hash IS NOT NULL
    );

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        operation = 'TRANSFER'
        OR (operation = 'SETTLEMENT' AND escrow_id IS NULL)
        OR (operation IN ('FUND', 'RELEASE', 'REFUND', 'CANCEL') AND escrow_id IS NOT NULL)
    );

COMMIT;
