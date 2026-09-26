-- Canonical value-movement integrity constraints.

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_operation_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_operation_check
    CHECK (operation IN ('FUND', 'RELEASE', 'REFUND', 'CANCEL', 'SETTLEMENT'));

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_integrity_hash_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_integrity_hash_check
    CHECK (integrity_hash IS NOT NULL AND length(integrity_hash) = 64);

ALTER TABLE gerchain_ledger_movements
    DROP CONSTRAINT IF EXISTS gerchain_movement_escrow_binding_check;

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_escrow_binding_check
    CHECK (escrow_id IS NOT NULL AND length(escrow_id) > 0);

ALTER TABLE gerchain_ledger_movements
    ADD CONSTRAINT gerchain_movement_distinct_accounts_check
    CHECK (source <> destination);

ALTER TABLE gerchain_idempotency_records
    ADD CONSTRAINT gerchain_idempotency_state_check
    CHECK (state IN ('PROCESSING', 'COMPLETED'));

ALTER TABLE gerchain_outbox_events
    ADD CONSTRAINT gerchain_outbox_state_check
    CHECK (state IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'));
