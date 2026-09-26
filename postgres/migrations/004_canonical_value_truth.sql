-- Canonical production value-truth persistence hardening.
CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow ON gerchain_ledger_movements (escrow_id);
CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_operation ON gerchain_ledger_movements (operation);
CREATE INDEX IF NOT EXISTS ix_gerchain_outbox_claim ON gerchain_outbox_events (state, lease_until, id);
CREATE INDEX IF NOT EXISTS ix_gerchain_idempotency_state ON gerchain_idempotency_records (state);