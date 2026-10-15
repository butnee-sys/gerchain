-- EA-35 idempotency schema compatibility hardening.
-- Reconciles legacy idempotency_key storage with the canonical key column.
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'gerchain_idempotency_records'
          AND column_name = 'key'
    ) THEN
        ALTER TABLE gerchain_idempotency_records
            ADD COLUMN key VARCHAR(255);

        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'gerchain_idempotency_records'
              AND column_name = 'idempotency_key'
        ) THEN
            EXECUTE 'UPDATE gerchain_idempotency_records SET key = idempotency_key WHERE key IS NULL';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM gerchain_idempotency_records
            WHERE key IS NULL
        ) THEN
            RAISE EXCEPTION 'cannot canonicalize idempotency records: NULL key remains';
        END IF;

        ALTER TABLE gerchain_idempotency_records
            ALTER COLUMN key SET NOT NULL;
    END IF;
END
$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_gerchain_idempotency_records_key
    ON gerchain_idempotency_records (key);

COMMIT;
