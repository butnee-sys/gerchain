-- Canonical GerChain production schema hardening.
-- Version 008: close witness and idempotency integrity gates required by production boot.

ALTER TABLE gerchain_transaction_witnesses
    DROP CONSTRAINT IF EXISTS gerchain_witness_amount_check;

ALTER TABLE gerchain_transaction_witnesses
    ADD CONSTRAINT gerchain_witness_amount_check
    CHECK (amount >= 0);

ALTER TABLE gerchain_idempotency_records
    DROP CONSTRAINT IF EXISTS gerchain_idempotency_state_check;

ALTER TABLE gerchain_idempotency_records
    ADD CONSTRAINT gerchain_idempotency_state_check
    CHECK (state IN ('PROCESSING', 'COMPLETED', 'FAILED'));

