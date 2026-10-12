-- EA-35.14: converge escrow state checks to exactly one canonical constraint.
-- Run after the legacy and EAI migrations. Safe to re-run on an already-converged schema.
-- Fails closed if existing escrow rows contain a non-canonical state.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM escrows
        WHERE state IS NULL
           OR state NOT IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED')
    ) THEN
        RAISE EXCEPTION 'EA-35.14 blocked: escrows contains NULL or non-canonical state values';
    END IF;
END $$;

DO $$
DECLARE c RECORD;
BEGIN
    FOR c IN
        SELECT pc.conname
        FROM pg_constraint pc
        JOIN pg_class t ON t.oid = pc.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = current_schema()
          AND t.relname = 'escrows'
          AND pc.contype = 'c'
          AND pg_get_constraintdef(pc.oid) ILIKE '%state%'
    LOOP
        EXECUTE format('ALTER TABLE %I.%I DROP CONSTRAINT %I',
                       current_schema(), 'escrows', c.conname);
    END LOOP;
END $$;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_canonical_check
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

DO $$
DECLARE state_checks INTEGER;
DECLARE canonical_checks INTEGER;
BEGIN
    SELECT COUNT(*) INTO state_checks
    FROM pg_constraint pc
    JOIN pg_class t ON t.oid = pc.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = current_schema()
      AND t.relname = 'escrows'
      AND pc.contype = 'c'
      AND pg_get_constraintdef(pc.oid) ILIKE '%state%';

    SELECT COUNT(*) INTO canonical_checks
    FROM pg_constraint pc
    JOIN pg_class t ON t.oid = pc.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = current_schema()
      AND t.relname = 'escrows'
      AND pc.conname = 'escrows_state_canonical_check'
      AND pc.contype = 'c';

    IF state_checks <> 1 OR canonical_checks <> 1 THEN
        RAISE EXCEPTION 'EA-35.14 failed: expected exactly one canonical escrow state constraint; found state_checks=%, canonical_checks=%',
            state_checks, canonical_checks;
    END IF;
END $$;

INSERT INTO schema_version(version, checksum)
VALUES (3, 'EA-35.14-single-canonical-escrow-state-constraint')
ON CONFLICT (version) DO UPDATE
SET checksum = EXCLUDED.checksum
WHERE schema_version.checksum = EXCLUDED.checksum;
