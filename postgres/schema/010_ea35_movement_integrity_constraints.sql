-- EA-35 canonical movement integrity constraints.
-- Immutable follow-up to migration 005.

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('FUND', 'RELEASE', 'REFUND', 'CANCEL', 'SETTLEMENT', 'TRANSFER'));

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (
        operation = 'TRANSFER'
        OR (integrity_hash IS NOT NULL AND length(integrity_hash) = 64)
    );

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        (operation = 'SETTLEMENT' AND escrow_id IS NULL)
        OR (operation <> 'SETTLEMENT' AND escrow_id IS NOT NULL)
    );
