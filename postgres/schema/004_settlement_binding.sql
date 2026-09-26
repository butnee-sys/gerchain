-- Canonical settlement binding correction.
-- Version 4: settlement is a direct ledger movement and therefore has no escrow_id.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        operation = 'SETTLEMENT'
        OR (escrow_id IS NOT NULL AND length(escrow_id) > 0)
    );
