-- Version 016: re-reconcile escrow state constraint on already-migrated databases.
-- Version 015 repaired drift at the time it was first applied. This follow-up
-- repairs databases where version 015 is recorded but a legacy state CHECK
-- remains (for example, because of out-of-band schema mutation or old bootstrap).
-- Invalid existing state values fail closed during VALIDATE.

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

    IF (
        SELECT COUNT(*)
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND contype = 'c'
          AND lower(pg_get_constraintdef(oid)) LIKE '%state%'
    ) <> 1 THEN
        RAISE EXCEPTION 'escrows.state must have exactly one canonical state CHECK constraint';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND conname = 'escrows_state_canonical_check'
          AND convalidated
    ) THEN
        RAISE EXCEPTION 'canonical escrow state constraint is absent or not validated';
    END IF;
END
$migration$;
