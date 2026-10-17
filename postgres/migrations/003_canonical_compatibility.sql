-- GerChain canonical production corrective migration 003
-- Adds compatibility-safe indexes after canonical columns/tables exist.
-- The escrow state invariant is owned by migration 005, which removes legacy
-- state CHECK constraints and installs exactly one canonical escrows_state_check.
-- Do not introduce a parallel state constraint here.

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow
    ON gerchain_ledger_movements (escrow_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_witness_escrow
    ON gerchain_transaction_witnesses (escrow_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_aggregate
    ON gerchain_outbox_events (aggregate_id);
