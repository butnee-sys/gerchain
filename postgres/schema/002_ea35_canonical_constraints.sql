-- EA-35.13 canonical production integrity constraints
-- This migration is additive and must remain immutable after application.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_operation_check;
ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT'));

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_integrity_hash_check;
ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (integrity_hash IS NOT NULL AND length(integrity_hash) = 64);

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_amount_check;
ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_amount_check
    CHECK (amount > 0);

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;
ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        (operation = 'SETTLEMENT' AND escrow_id IS NULL)
        OR
        (operation <> 'SETTLEMENT' AND escrow_id IS NOT NULL)
    );

ALTER TABLE gerchain_transaction_witnesses
    DROP CONSTRAINT IF EXISTS gerchain_witness_amount_check;
ALTER TABLE gerchain_transaction_witnesses
    ADD CONSTRAINT gerchain_witness_amount_check
    CHECK (amount >= 0);

ALTER TABLE gerchain_idempotency_records
    DROP CONSTRAINT IF EXISTS gerchain_idempotency_state_check;
ALTER TABLE gerchain_idempotency_records
    ADD CONSTRAINT gerchain_idempotency_state_check
    CHECK (state IN ('PROCESSING','COMPLETED'));
