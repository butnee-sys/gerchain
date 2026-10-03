-- Canonical production value-authority hardening.
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT, ADD COLUMN IF NOT EXISTS currency TEXT, ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
DO $$ BEGIN IF EXISTS (SELECT 1 FROM escrows WHERE currency IS NULL) THEN RAISE EXCEPTION 'canonical migration requires escrow currency backfill before authority cutover'; END IF; END $$;
UPDATE escrows SET refund_destination = sender_address WHERE refund_destination IS NULL;
ALTER TABLE escrows ALTER COLUMN refund_destination SET NOT NULL, ALTER COLUMN currency SET NOT NULL;
DO $$ DECLARE constraint_name TEXT; BEGIN FOR constraint_name IN SELECT conname FROM pg_constraint WHERE conrelid='escrows'::regclass AND contype='c' AND pg_get_constraintdef(oid) LIKE '%state%' LOOP EXECUTE format('ALTER TABLE escrows DROP CONSTRAINT %I', constraint_name); END LOOP; END $$;
ALTER TABLE escrows ADD CONSTRAINT ck_escrows_canonical_state CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));