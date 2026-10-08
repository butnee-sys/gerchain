-- Canonical production evidence constraints.
-- Version 010: close integrity gaps required by the production schema guard.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_amount_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_amount_check
    CHECK (amount > 0);

ALTER TABLE gerchain_transaction_witnesses
    DROP CONSTRAINT IF EXISTS gerchain_witness_amount_check;

ALTER TABLE gerchain_transaction_witnesses
    ADD CONSTRAINT gerchain_witness_amount_check
    CHECK (amount >= 0);

ALTER TABLE gerchain_idempotency_records
    DROP CONSTRAINT IF EXISTS gerchain_idempotency_state_check;

ALTER TABLE gerchain_idempotency_records
    ADD CONSTRAINT gerchain_idempotency_state_check
    CHECK (state IN ('PROCESSING', 'COMPLETED'));

ALTER TABLE gerchain_ledger_accounts
    DROP CONSTRAINT IF EXISTS gerchain_ledger_balance_check;

ALTER TABLE gerchain_ledger_accounts
    ADD CONSTRAINT gerchain_ledger_balance_check
    CHECK (balance >= 0);

ALTER TABLE gerchain_ledger_accounts
    DROP CONSTRAINT IF EXISTS gerchain_ledger_version_check;

ALTER TABLE gerchain_ledger_accounts
    ADD CONSTRAINT gerchain_ledger_version_check
    CHECK (version >= 0);

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
