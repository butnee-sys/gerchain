-- EA-35 canonical movement integrity contract.
-- Adds the fields required by the authoritative value-truth graph.
-- Existing rows with incomplete evidence fail closed; no evidence is fabricated.

BEGIN;

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS operation VARCHAR(32);

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS escrow_id VARCHAR(128);

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(128);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM gerchain_ledger_movements
        WHERE operation IS NULL
           OR integrity_hash IS NULL
           OR length(integrity_hash) <> 64
    ) THEN
        RAISE EXCEPTION
            'existing ledger movements lack canonical operation/integrity evidence; reconciliation required before migration';
    END IF;
END
$$;

ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN operation SET NOT NULL;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('FUND', 'RELEASE', 'REFUND', 'CANCEL', 'SETTLEMENT'));

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_amount_check
    CHECK (amount > 0);

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (integrity_hash ~ '^[0-9a-f]{64}$');

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        (operation = 'SETTLEMENT' AND escrow_id IS NULL)
        OR
        (operation IN ('FUND', 'RELEASE', 'REFUND', 'CANCEL') AND escrow_id IS NOT NULL)
    );

ALTER TABLE gerchain_transaction_witnesses
    ADD CONSTRAINT gerchain_witness_amount_check
    CHECK (amount >= 0);

COMMIT;
