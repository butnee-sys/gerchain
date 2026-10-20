-- Safe canonical escrow constraints.
-- Fail closed: do not infer currency for legacy rows and do not rewrite states.
DO $migration$
DECLARE
    invalid_states TEXT;
    missing_currency BIGINT;
BEGIN
    SELECT string_agg(DISTINCT state, ', ' ORDER BY state)
      INTO invalid_states
      FROM escrows
     WHERE state IS NULL
        OR state NOT IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED');

    IF invalid_states IS NOT NULL THEN
        RAISE EXCEPTION
            'escrow constraint migration blocked: unsupported state(s): %',
            invalid_states;
    END IF;

    SELECT count(*) INTO missing_currency
      FROM escrows
     WHERE currency IS NULL OR btrim(currency) = '';

    IF missing_currency > 0 THEN
        RAISE EXCEPTION
            'escrow constraint migration blocked: % row(s) have missing currency; provide reviewed, authoritative currency mapping before retry',
            missing_currency;
    END IF;
END
$migration$;

-- The checks above intentionally precede any constraint mutation.
ALTER TABLE escrows ALTER COLUMN currency SET NOT NULL;

ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check;
ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_check
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_currency_nonblank_check;
ALTER TABLE escrows
    ADD CONSTRAINT escrows_currency_nonblank_check
    CHECK (btrim(currency) <> '');
