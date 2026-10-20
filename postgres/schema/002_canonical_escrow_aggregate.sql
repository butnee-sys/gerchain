-- Canonical escrow aggregate compatibility migration.
-- Apply only after taking a PostgreSQL backup and recording a pre-migration
-- reconciliation snapshot. This migration does not move value.
--
-- Legacy escrows use the same table name but support only CREATED/LOCKED/
-- RELEASED. The canonical aggregate requires the full lifecycle and metadata.
-- Currency is intentionally NOT inferred: operators must backfill it from
-- authoritative transaction evidence before enabling value-moving operations.
BEGIN;

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;

-- Preserve the best existing creation-time evidence available in the legacy
-- schema. This is a migration fallback, not proof of the original creation time.
UPDATE escrows
SET created_at = COALESCE(updated_at, now())
WHERE created_at IS NULL;

ALTER TABLE escrows
    ALTER COLUMN created_at SET DEFAULT now(),
    ALTER COLUMN created_at SET NOT NULL;

-- The legacy sender is the only recorded origin address. Backfill refund
-- destination from it, then require reconciliation against source evidence
-- before production release. Never derive currency from amount or address.
UPDATE escrows
SET refund_destination = sender_address
WHERE refund_destination IS NULL;

ALTER TABLE escrows
    DROP CONSTRAINT IF EXISTS escrows_state_check;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN (
        'CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'
    )) NOT VALID;

ALTER TABLE escrows
    VALIDATE CONSTRAINT escrows_state_check;

CREATE INDEX IF NOT EXISTS ix_escrows_state_updated_at
    ON escrows (state, updated_at);

COMMIT;

-- POST-MIGRATION GATES (must be checked by deployment automation):
-- 1. currency IS NOT NULL for every escrow eligible for value movement.
-- 2. refund_destination is reconciled to authoritative funding-origin evidence.
-- 3. existing states and row counts reconcile to the pre-migration snapshot.
-- 4. ledger movements, witnesses, outbox events and idempotency records reconcile.
-- 5. do not treat metadata.create_all() as a substitute for applying migrations.
