-- Canonical production evidence constraints.
-- Version 010: close integrity gaps required by the production schema guard.
--
-- Constraint replacement is performed inside PostgreSQL DO blocks so DROP and
-- ADD execute sequentially on the server. This is required when migration SQL
-- is submitted as one batch through psycopg/SQLAlchemy.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_amount_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_amount_check CHECK (amount > 0);

DO $$
BEGIN
    EXECUTE 'ALTER TABLE gerchain_transaction_witnesses DROP CONSTRAINT IF EXISTS gerchain_witness_amount_check';
    EXECUTE 'ALTER TABLE gerchain_transaction_witnesses ADD CONSTRAINT gerchain_witness_amount_check CHECK (amount >= 0)';
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER TABLE gerchain_idempotency_records DROP CONSTRAINT IF EXISTS gerchain_idempotency_state_check';
    EXECUTE 'ALTER TABLE gerchain_idempotency_records ADD CONSTRAINT gerchain_idempotency_state_check CHECK (state IN (''PROCESSING'', ''COMPLETED''))';
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER TABLE gerchain_ledger_accounts DROP CONSTRAINT IF EXISTS gerchain_ledger_balance_check';
    EXECUTE 'ALTER TABLE gerchain_ledger_accounts ADD CONSTRAINT gerchain_ledger_balance_check CHECK (balance >= 0)';
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER TABLE gerchain_ledger_accounts DROP CONSTRAINT IF EXISTS gerchain_ledger_version_check';
    EXECUTE 'ALTER TABLE gerchain_ledger_accounts ADD CONSTRAINT gerchain_ledger_version_check CHECK (version >= 0)';
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER TABLE gerchain_ledger_movements DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check';
    EXECUTE 'ALTER TABLE gerchain_ledger_movements ADD CONSTRAINT gerchain_movement_escrow_binding_check CHECK (
        (operation = ''SETTLEMENT'' AND escrow_id IS NULL)
        OR (
            operation IN (''FUND'', ''RELEASE'', ''REFUND'', ''CANCEL'')
            AND escrow_id IS NOT NULL
            AND length(escrow_id) > 0
        )
    )';
END $$;
