-- Canonical value-flow integrity constraints.
-- These constraints fail closed if existing production data violates the
-- canonical movement contract. No value is moved by this migration.

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('FUND', 'RELEASE', 'REFUND', 'CANCEL', 'SETTLEMENT'));

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (integrity_hash IS NOT NULL AND length(integrity_hash) = 64);

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        (operation = 'SETTLEMENT' AND escrow_id IS NULL)
        OR
        (operation IN ('FUND', 'RELEASE', 'REFUND', 'CANCEL') AND escrow_id IS NOT NULL)
    );
