-- EA-35 PostgreSQL compatibility repair.
-- Ensures the authoritative ORM column exists on any pre-existing table.

ALTER TABLE gerchain_idempotency_records
    ADD COLUMN IF NOT EXISTS key VARCHAR(255);

UPDATE gerchain_idempotency_records
SET key = COALESCE(key, id::TEXT)
WHERE key IS NULL;

ALTER TABLE gerchain_idempotency_records
    ALTER COLUMN key SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_gerchain_idempotency_key
    ON gerchain_idempotency_records (key);
