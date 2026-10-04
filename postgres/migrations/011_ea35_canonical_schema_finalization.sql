-- EA-35 canonical schema finalization.
-- Brings PostgreSQL installations to the exact durable contract used by the
-- production ORM. No value movement is performed.
--
-- Existing rows are never assigned fabricated currency or refund-destination metadata.
-- If legacy rows lack either required canonical value, the migration fails closed.
--
-- Constraint replacement is performed inside PostgreSQL DO blocks so DROP and
-- ADD execute sequentially on the server when the migration is submitted as
-- one SQL batch.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;

UPDATE escrows
SET created_at = COALESCE(created_at, updated_at, now())
WHERE created_at IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM escrows
        WHERE currency IS NULL OR refund_destination IS NULL OR created_at IS NULL
    ) THEN
        RAISE EXCEPTION
            'EA-35 canonical finalization blocked: existing escrow rows lack required currency/refund/created_at metadata';
    END IF;
END $$;

ALTER TABLE escrows
    ALTER COLUMN refund_destination SET NOT NULL,
    ALTER COLUMN currency SET NOT NULL,
    ALTER COLUMN version SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL;

DO $$
BEGIN
    EXECUTE 'ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check';
    EXECUTE 'ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_canonical_check';
    EXECUTE 'ALTER TABLE escrows ADD CONSTRAINT escrows_state_canonical_check CHECK (state IN (''CREATED'', ''FUNDED'', ''LOCKED'', ''RELEASED'', ''REFUNDED'', ''CANCELLED''))';
END $$;

ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN integrity_hash SET NOT NULL;

DO $$
BEGIN
    EXECUTE 'ALTER TABLE gerchain_ledger_movements DROP CONSTRAINT IF EXISTS gerchain_movement_operation_check';
    EXECUTE 'ALTER TABLE gerchain_ledger_movements DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check';
    EXECUTE 'ALTER TABLE gerchain_ledger_movements DROP CONSTRAINT IF EXISTS gerchain_movement_integrity_hash_check';
    EXECUTE 'ALTER TABLE gerchain_ledger_movements DROP CONSTRAINT IF EXISTS gerchain_movement_amount_check';
    EXECUTE 'ALTER TABLE gerchain_ledger_movements ADD CONSTRAINT gerchain_movement_operation_check CHECK (operation IN (''FUND'', ''RELEASE'', ''REFUND'', ''CANCEL'', ''SETTLEMENT''))';
    EXECUTE 'ALTER TABLE gerchain_ledger_movements ADD CONSTRAINT gerchain_movement_integrity_hash_check CHECK (length(integrity_hash) = 64)';
    EXECUTE 'ALTER TABLE gerchain_ledger_movements ADD CONSTRAINT gerchain_movement_escrow_binding_check CHECK (
        (operation = ''SETTLEMENT'' AND escrow_id IS NULL)
        OR (
            operation IN (''FUND'', ''RELEASE'', ''REFUND'', ''CANCEL'')
            AND escrow_id IS NOT NULL
            AND length(escrow_id) > 0
        )
    )';
    EXECUTE 'ALTER TABLE gerchain_ledger_movements ADD CONSTRAINT gerchain_movement_amount_check CHECK (amount > 0)';
END $$;

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

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow
    ON gerchain_ledger_movements (escrow_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_events_aggregate
    ON gerchain_outbox_events (aggregate_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_idempotency_state
    ON gerchain_idempotency_records (state);
