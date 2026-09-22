-- Canonical escrow lifecycle migration.
-- Extends legacy escrow storage to the frozen durable aggregate contract.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency TEXT,
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

UPDATE escrows
SET refund_destination = COALESCE(refund_destination, sender_address),
    currency = COALESCE(currency, 'MNT'),
    created_at = COALESCE(created_at, updated_at, now()),
    version = COALESCE(version, 0);

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    FOR constraint_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND contype = 'c'
          AND strpos(pg_get_constraintdef(oid), 'state') > 0
    LOOP
        EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT %I', constraint_name);
    END LOOP;
END $$;

ALTER TABLE escrows
    ALTER COLUMN refund_destination SET NOT NULL,
    ALTER COLUMN currency SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN version SET NOT NULL,
    ADD CONSTRAINT escrows_state_canonical_check
        CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

ALTER TABLE escrows
    ALTER COLUMN amount SET NOT NULL;
