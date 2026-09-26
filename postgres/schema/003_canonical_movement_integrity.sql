-- Canonical movement integrity constraints.
-- Separate migration so applied migration checksums remain immutable.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'gerchain_movement_operation_check'
    ) THEN
        ALTER TABLE gerchain_ledger_movements
        ADD CONSTRAINT gerchain_movement_operation_check
        CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'gerchain_movement_integrity_hash_check'
    ) THEN
        ALTER TABLE gerchain_ledger_movements
        ADD CONSTRAINT gerchain_movement_integrity_hash_check
        CHECK (integrity_hash IS NOT NULL AND length(integrity_hash) = 64);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'gerchain_movement_escrow_binding_check'
    ) THEN
        ALTER TABLE gerchain_ledger_movements
        ADD CONSTRAINT gerchain_movement_escrow_binding_check
        CHECK (
            (operation = 'SETTLEMENT' AND escrow_id IS NULL)
            OR
            (operation IN ('FUND','RELEASE','REFUND','CANCEL') AND escrow_id IS NOT NULL)
        );
    END IF;
END $$;
