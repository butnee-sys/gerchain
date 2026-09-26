-- EA-35 canonical settlement binding correction.
-- SETTLEMENT is a direct Canonical Ledger movement and is intentionally
-- not bound to an escrow aggregate. Escrow-bound value operations remain
-- FUND, RELEASE, REFUND and CANCEL.
--
-- This is a new migration rather than an edit to 003, preserving checksum
-- immutability for already-applied production migrations.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (
        (operation = 'SETTLEMENT' AND escrow_id IS NULL)
        OR (
            operation IN ('FUND', 'RELEASE', 'REFUND', 'CANCEL')
            AND escrow_id IS NOT NULL
            AND length(escrow_id) > 0
        )
    );
