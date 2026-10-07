-- EA-35 canonical production schema hardening.
-- Version 13: database-level invariants for canonical value truth.
-- No value movement is performed.

ALTER TABLE gerchain_ledger_accounts
    DROP CONSTRAINT IF EXISTS gerchain_ledger_balance_nonnegative,
    ADD CONSTRAINT gerchain_ledger_balance_nonnegative CHECK (balance >= 0);

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_distinct_accounts,
    ADD CONSTRAINT gerchain_movement_distinct_accounts CHECK (source <> destination);

ALTER TABLE gerchain_transaction_witnesses
    DROP CONSTRAINT IF EXISTS gerchain_witness_event_type_check,
    ADD CONSTRAINT gerchain_witness_event_type_check CHECK (
        event_type IN (
            'GERCHAIN_FUNDED',
            'GERCHAIN_LOCKED',
            'GERCHAIN_RELEASED',
            'GERCHAIN_REFUNDED',
            'GERCHAIN_CANCELLED',
            'GERCHAIN_SETTLED'
        )
    );

ALTER TABLE gerchain_outbox_events
    DROP CONSTRAINT IF EXISTS gerchain_outbox_state_check,
    ADD CONSTRAINT gerchain_outbox_state_check CHECK (
        state IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')
    );

ALTER TABLE gerchain_idempotency_records
    DROP CONSTRAINT IF EXISTS gerchain_idempotency_fingerprint_check,
    ADD CONSTRAINT gerchain_idempotency_fingerprint_check CHECK (length(fingerprint) = 64);

ALTER TABLE escrows
    DROP CONSTRAINT IF EXISTS escrows_amount_positive_check,
    ADD CONSTRAINT escrows_amount_positive_check CHECK (amount > 0);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM escrows
        WHERE currency IS NULL OR refund_destination IS NULL OR created_at IS NULL
    ) THEN
        RAISE EXCEPTION 'EA-35 canonical hardening blocked: escrow canonical metadata is incomplete';
    END IF;
END $$;

ALTER TABLE escrows
    ALTER COLUMN currency SET NOT NULL,
    ALTER COLUMN refund_destination SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_transaction
    ON gerchain_ledger_movements (transaction_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_witnesses_transaction
    ON gerchain_transaction_witnesses (transaction_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_idempotency_key
    ON gerchain_idempotency_records (key);
