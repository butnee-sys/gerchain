-- GerChain canonical production corrective migration 003
-- Adds only compatibility-safe constraints after canonical columns/tables exist.
-- No existing value row is rejected by this migration.

ALTER TABLE escrows DROP CONSTRAINT IF EXISTS gerchain_escrow_state_check;
ALTER TABLE escrows ADD CONSTRAINT gerchain_escrow_state_check
    CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow
    ON gerchain_ledger_movements (escrow_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_witness_escrow
    ON gerchain_transaction_witnesses (escrow_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_aggregate
    ON gerchain_outbox_events (aggregate_id);
