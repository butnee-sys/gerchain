-- Version 014: retire the stale legacy escrow state constraint.
-- Additive migration: never rewrite migrations 001-013 or their recorded checksums.
-- Idempotent on both fresh installs and databases that already have the canonical check.

DO $migration$
BEGIN
    IF to_regclass('escrows') IS NULL THEN
        RAISE EXCEPTION 'required table escrows does not exist; apply canonical migrations first';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND conname = 'legacy_escrow_state_check'
    ) THEN
        ALTER TABLE escrows
            DROP CONSTRAINT legacy_escrow_state_check;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND conname = 'escrows_state_canonical_check'
    ) THEN
        ALTER TABLE escrows
            ADD CONSTRAINT escrows_state_canonical_check
            CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));
    END IF;
END
$migration$;
