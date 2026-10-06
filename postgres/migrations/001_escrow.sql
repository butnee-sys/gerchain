CREATE TABLE IF NOT EXISTS escrows (
    id TEXT PRIMARY KEY,
    sender_address TEXT NOT NULL,
    receiver_address TEXT NOT NULL,
    amount NUMERIC(38,8) NOT NULL CHECK (amount > 0),
    state TEXT NOT NULL CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED')),
    condition_desc TEXT,
    refund_destination TEXT,
    currency TEXT,
    version BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
