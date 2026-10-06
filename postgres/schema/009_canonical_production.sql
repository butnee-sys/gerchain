-- Canonical GerChain production schema hardening.
-- Version 009: enforce strictly positive canonical value movement.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_amount_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_amount_check
    CHECK (amount > 0);
