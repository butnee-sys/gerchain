-- Version 003: remove the stale legacy escrow state constraint without
-- rewriting any previously applied migration (preserves historical checksums).
-- Safe to re-run: the obsolete constraint is dropped only when present, and
-- the canonical constraint is added only when absent.
--
-- Expected canonical lifecycle:
-- CREATED -> FUNDED -> LOCKED -> RELEASED / REFUNDED
-- CREATED or FUNDED -> CANCELLED (with value reversal for FUNDED).

BEGIN;

DO $migration$
BEGIN
    IF to_regclass('public.escrows') IS NULL THEN
        RAISE EXCEPTION 'required table public.escrows does not exist; apply base schema first';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'public.escrows'::regclass
          AND c.conname = 'legacy_escrow_state_check'
    ) THEN
        ALTER TABLE public.escrows
            DROP CONSTRAINT legacy_escrow_state_check;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'public.escrows'::regclass
          AND c.conname = 'escrows_state_canonical_check'
    ) THEN
        ALTER TABLE public.escrows
            ADD CONSTRAINT escrows_state_canonical_check
            CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));
    END IF;
END
$migration$;

COMMIT;
