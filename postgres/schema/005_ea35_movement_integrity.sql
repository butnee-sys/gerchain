-- EA-35 canonical movement evidence hardening.
-- Structural only; no value movement.
--
-- The ORM now treats operation, escrow_id, and integrity_hash as part of
-- canonical movement evidence. Existing rows remain readable and must be
-- reconciled before production authority is locked.

BEGIN;

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS operation VARCHAR(32) NOT NULL DEFAULT 'TRANSFER';

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS escrow_id VARCHAR(128);

ALTER TABLE gerchain_ledger_movements
    ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(128);

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_escrow
    ON gerchain_ledger_movements (escrow_id);

CREATE INDEX IF NOT EXISTS ix_gerchain_ledger_movements_operation
    ON gerchain_ledger_movements (operation);

COMMIT;
