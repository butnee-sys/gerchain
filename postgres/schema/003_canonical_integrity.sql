-- Canonical production integrity constraints
-- Version 3: bind value movements to valid operations and evidence shape.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_operation_check,
    DROP CONSTRAINT IF EXISTS gerchain_movement_integrity_hash_check,
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('FUND','RELEASE','REFUND','CANCEL','SETTLEMENT','TRANSFER')),
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (integrity_hash IS NOT NULL AND length(integrity_hash) = 64),
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (operation = 'SETTLEMENT' OR escrow_id IS NOT NULL);

ALTER TABLE gerchain_idempotency_records
    ADD CONSTRAINT gerchain_idempotency_fingerprint_check
    CHECK (length(fingerprint) = 64),
    ADD CONSTRAINT gerchain_idempotency_state_check
    CHECK (state IN ('PROCESSING','COMPLETED'));

ALTER TABLE gerchain_outbox_events
    ADD CONSTRAINT gerchain_outbox_state_check
    CHECK (state IN ('PENDING','PROCESSING','COMPLETED'));

ALTER TABLE gerchain_transaction_witnesses
    ADD CONSTRAINT gerchain_witness_event_check
    CHECK (event_type IN ('GERCHAIN_FUND','GERCHAIN_LOCKED','GERCHAIN_RELEASED','GERCHAIN_REFUNDED','GERCHAIN_CANCELLED','GERCHAIN_SETTLED'));

CREATE INDEX IF NOT EXISTS ix_gerchain_idempotency_key
    ON gerchain_idempotency_records (key);
