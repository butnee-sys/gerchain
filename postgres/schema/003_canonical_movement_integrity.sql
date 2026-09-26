-- Canonical movement integrity constraints.
-- This migration is additive and preserves the checksum of 002.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_operation_check,
    DROP CONSTRAINT IF EXISTS gerchain_movement_integrity_hash_check,
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('TRANSFER','FUND','RELEASE','REFUND','CANCEL','SETTLEMENT'));

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (
        operation = 'TRANSFER'
        OR (integrity_hash IS NOT NULL AND length(integrity_hash) = 64)
    );

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        operation = 'TRANSFER'
        OR escrow_id IS NOT NULL
    );
