-- Canonical movement integrity hardening after legacy-compatible migration 003.
-- Version 009 is additive and preserves prior migration checksums.
-- Existing constraints are replaced with the strict canonical production contract.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_operation_check,
    DROP CONSTRAINT IF EXISTS gerchain_movement_integrity_hash_check,
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;

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
