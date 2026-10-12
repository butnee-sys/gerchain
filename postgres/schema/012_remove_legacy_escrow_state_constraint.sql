-- Remove the historical state check left by the legacy concurrency schema.
-- EA-35 canonical finalization installs escrows_state_canonical_check, which
-- already validates the complete lifecycle. Keeping both constraints leaves
-- incompatible lifecycle authorities on the same durable aggregate.
ALTER TABLE escrows
    DROP CONSTRAINT IF EXISTS legacy_escrow_state_check;
