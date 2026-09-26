-- Canonical production persistence reconciliation hardening.
ALTER TABLE escrows ADD COLUMN IF NOT EXISTS refund_destination TEXT, ADD COLUMN IF NOT EXISTS currency TEXT, ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
UPDATE escrows SET created_at=COALESCE(created_at,updated_at,now()), currency=COALESCE(currency,'MNT'), version=COALESCE(version,0), refund_destination=COALESCE(refund_destination,sender_address);
ALTER TABLE escrows ALTER COLUMN currency SET NOT NULL;
ALTER TABLE escrows DROP CONSTRAINT IF EXISTS escrows_state_check, DROP CONSTRAINT IF EXISTS escrows_state_canonical_check;
ALTER TABLE escrows ADD CONSTRAINT escrows_state_check CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'));