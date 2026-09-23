-- EA-35 PostgreSQL compatibility repair.
-- Normalizes the durable idempotency column name to the authoritative ORM contract.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'gerchain_idempotency_records'
          AND column_name = 'idempotency_key'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'gerchain_idempotency_records'
          AND column_name = 'key'
    ) THEN
        ALTER TABLE gerchain_idempotency_records
            RENAME COLUMN idempotency_key TO key;
    END IF;
END $$;

ALTER TABLE gerchain_idempotency_records
    ADD COLUMN IF NOT EXISTS key VARCHAR(255);

UPDATE gerchain_idempotency_records
SET key = COALESCE(key, id::TEXT)
WHERE key IS NULL;

ALTER TABLE gerchain_idempotency_records
    ALTER COLUMN key SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_gerchain_idempotency_key
    ON gerchain_idempotency_records (key);
