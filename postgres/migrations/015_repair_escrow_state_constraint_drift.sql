-- Version 015: repair stale escrow state CHECK constraints before production boot.
-- Do not edit migrations 001-014 or their published checksums.
-- The migration intentionally normalizes every CHECK that constrains escrows.state,
-- not only historically known generated names, then verifies the canonical CHECK.
-- Invalid legacy rows fail validation and therefore block migration/production boot.

DO $migration$
DECLARE
    item RECORD;
BEGIN
    IF to_regclass('escrows') IS NULL THEN
        RAISE EXCEPTION 'required table escrows does not exist; apply canonical migrations first';
    END IF;

    FOR item IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND contype = 'c'
          AND lower(pg_get_constraintdef(oid)) LIKE '%state%'
          AND conname <> 'escrows_state_canonical_check'
    LOOP
        EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT %I', item.conname);
    END LOOP;

    -- Rebuild the canonical constraint from the declared lifecycle invariant.
    -- This also repairs a same-named constraint whose definition drifted.
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND conname = 'escrows_state_canonical_check'
    ) THEN
        ALTER TABLE escrows DROP CONSTRAINT escrows_state_canonical_check;
    END IF;

    ALTER TABLE escrows
        ADD CONSTRAINT escrows_state_canonical_check
        CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'))
        NOT VALID;

    ALTER TABLE escrows VALIDATE CONSTRAINT escrows_state_canonical_check;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND conname = 'escrows_state_canonical_check'
          AND convalidated
    ) THEN
        RAISE EXCEPTION 'canonical escrow state constraint is absent or not validated';
    END IF;
END
$migration$;
