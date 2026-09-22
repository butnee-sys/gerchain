-- EA-25 durable idempotency
-- Structural only. No value movement.
CREATE TABLE IF NOT EXISTS gerchain_idempotency_records (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    fingerprint VARCHAR(64) NOT NULL,
    result_json TEXT NULL,
    state VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT gerchain_idempotency_state_check
        CHECK (state IN ('PROCESSING', 'COMPLETED'))
);

CREATE INDEX IF NOT EXISTS ix_gerchain_idempotency_state
    ON gerchain_idempotency_records (state);

