-- Canonical EAI production schema reconciliation for PostgreSQL.
-- Idempotent. Does not invent value ownership or migrate balances.

ALTER TABLE escrows
    ADD COLUMN IF NOT EXISTS refund_destination TEXT,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(16),
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE escrows
    ALTER COLUMN updated_at SET DEFAULT now();

DO $$
DECLARE c RECORD;
BEGIN
    FOR c IN
        SELECT conname
        FROM pg_constraint pc
        JOIN pg_class t ON t.oid = pc.conrelid
        WHERE t.relname = 'escrows'
          AND pc.contype = 'c'
          AND pg_get_constraintdef(pc.oid) LIKE '%state%'
    LOOP
        EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT IF EXISTS %I', c.conname);
    END LOOP;
END $$;

ALTER TABLE escrows
    ADD CONSTRAINT escrows_state_canonical_check
    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'));

CREATE INDEX IF NOT EXISTS ix_escrows_state ON escrows(state);
CREATE INDEX IF NOT EXISTS ix_escrows_updated_at ON escrows(updated_at);

-- Canonical production tables are created by SQLAlchemy metadata; this migration
-- only reconciles the legacy escrow table that predates the canonical aggregate.
