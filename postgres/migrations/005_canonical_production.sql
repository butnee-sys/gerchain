-- Canonical production schema hardening.
-- Version 002 establishes the canonical persistence tables; this migration
-- makes the production lifecycle schema explicit and repeatable.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    FOR constraint_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND contype = 'c'
          AND pg_get_constraintdef(oid) LIKE '%state%'
    LOOP
        EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT %I', constraint_name);
    END LOOP;
END $$;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_accounts_currency
    ON gerchain_ledger_accounts (currency);

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_transaction
    ON gerchain_ledger_movements (transaction_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow_operation
    ON gerchain_ledger_movements (escrow_id, operation);

CREATE INDEX IF NOT EXISTS ix_gerchain_witness_transaction
    ON gerchain_transaction_witnesses (transaction_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_idempotency_state
    ON gerchain_idempotency_records (state, updated_at);
