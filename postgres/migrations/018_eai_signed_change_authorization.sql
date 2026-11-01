-- C-01: durable authorization evidence for cryptographically signed RELEASE.
-- Version 18. This table is append-only authorization evidence; it does not
-- replace ledger movements, transaction witnesses, or idempotency records.
CREATE TABLE gerchain_authorization_changes (
    change_id VARCHAR(255) PRIMARY KEY,
    owner_id VARCHAR(128) NOT NULL,
    operation VARCHAR(16) NOT NULL,
    transaction_id VARCHAR(128) NOT NULL,
    escrow_id VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    payload_hash CHAR(64) NOT NULL,
    signature TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT gerchain_authorization_operation_check
        CHECK (operation IN ('RELEASE', 'REFUND', 'CANCEL')),
    CONSTRAINT gerchain_authorization_version_check
        CHECK (version > 0),
    CONSTRAINT gerchain_authorization_payload_hash_check
        CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT gerchain_authorization_signature_check
        CHECK (length(signature) > 0),
    CONSTRAINT gerchain_authorization_operation_transaction_uq
        UNIQUE (operation, transaction_id)
);
