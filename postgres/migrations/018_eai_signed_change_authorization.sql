-- C-01: durable authorization evidence for cryptographically signed RELEASE/REFUND.
-- Version 18. The migration is the sole production schema authority. It also
-- reconciles a structurally compatible pre-existing table without masking drift.
CREATE TABLE IF NOT EXISTS gerchain_authorization_changes (
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

DO $$
DECLARE
    table_oid REGCLASS;
    incompatible_columns TEXT[];
BEGIN
    table_oid := to_regclass('gerchain_authorization_changes');
    IF table_oid IS NULL THEN
        RAISE EXCEPTION 'canonical SignedChange table was not created in current_schema()';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'gerchain_authorization_changes'
    ) <> 9 THEN
        RAISE EXCEPTION
            'pre-existing gerchain_authorization_changes must have exactly 9 canonical columns';
    END IF;

    SELECT array_agg(expected.column_name ORDER BY expected.column_name)
    INTO incompatible_columns
    FROM (VALUES
        ('change_id', 'character varying', 255::integer, 'NO'),
        ('owner_id', 'character varying', 128::integer, 'NO'),
        ('operation', 'character varying', 16::integer, 'NO'),
        ('transaction_id', 'character varying', 128::integer, 'NO'),
        ('escrow_id', 'character varying', 255::integer, 'NO'),
        ('version', 'integer', NULL::integer, 'NO'),
        ('payload_hash', 'character', 64::integer, 'NO'),
        ('signature', 'text', NULL::integer, 'NO'),
        ('created_at', 'timestamp with time zone', NULL::integer, 'NO')
    ) AS expected(column_name, data_type, max_length, is_nullable)
    LEFT JOIN information_schema.columns AS actual
      ON actual.table_schema = current_schema()
     AND actual.table_name = 'gerchain_authorization_changes'
     AND actual.column_name = expected.column_name
    WHERE actual.column_name IS NULL
       OR actual.data_type <> expected.data_type
       OR actual.character_maximum_length IS DISTINCT FROM expected.max_length
       OR actual.is_nullable <> expected.is_nullable;

    IF incompatible_columns IS NOT NULL THEN
        RAISE EXCEPTION
            'pre-existing gerchain_authorization_changes has incompatible columns: %',
            incompatible_columns;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid
          AND contype = 'p'
          AND pg_get_constraintdef(oid) <> 'PRIMARY KEY (change_id)'
    ) THEN
        RAISE EXCEPTION 'pre-existing SignedChange table has a non-canonical primary key';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid AND contype = 'p'
    ) THEN
        ALTER TABLE gerchain_authorization_changes
            ADD CONSTRAINT gerchain_authorization_changes_pkey PRIMARY KEY (change_id);
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid
          AND conname = 'gerchain_authorization_operation_transaction_uq'
          AND (
              contype <> 'u'
              OR pg_get_constraintdef(oid) <> 'UNIQUE (operation, transaction_id)'
          )
    ) THEN
        RAISE EXCEPTION 'pre-existing SignedChange operation/transaction constraint is incompatible';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid
          AND conname = 'gerchain_authorization_operation_transaction_uq'
          AND contype = 'u'
    ) THEN
        ALTER TABLE gerchain_authorization_changes
            ADD CONSTRAINT gerchain_authorization_operation_transaction_uq
            UNIQUE (operation, transaction_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid AND conname = 'gerchain_authorization_operation_check'
    ) THEN
        ALTER TABLE gerchain_authorization_changes
            ADD CONSTRAINT gerchain_authorization_operation_check
            CHECK (operation IN ('RELEASE', 'REFUND', 'CANCEL'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid AND conname = 'gerchain_authorization_version_check'
    ) THEN
        ALTER TABLE gerchain_authorization_changes
            ADD CONSTRAINT gerchain_authorization_version_check CHECK (version > 0);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid AND conname = 'gerchain_authorization_payload_hash_check'
    ) THEN
        ALTER TABLE gerchain_authorization_changes
            ADD CONSTRAINT gerchain_authorization_payload_hash_check
            CHECK (payload_hash ~ '^[0-9a-f]{64}$');
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid AND conname = 'gerchain_authorization_signature_check'
    ) THEN
        ALTER TABLE gerchain_authorization_changes
            ADD CONSTRAINT gerchain_authorization_signature_check
            CHECK (length(signature) > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid
          AND conname = 'gerchain_authorization_operation_check'
          AND contype = 'c'
          AND convalidated
          AND position('operation' in lower(pg_get_constraintdef(oid))) > 0
          AND position('release' in lower(pg_get_constraintdef(oid))) > 0
          AND position('refund' in lower(pg_get_constraintdef(oid))) > 0
          AND position('cancel' in lower(pg_get_constraintdef(oid))) > 0
    ) THEN
        RAISE EXCEPTION 'SignedChange operation CHECK is missing or weakened';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid
          AND conname = 'gerchain_authorization_version_check'
          AND contype = 'c'
          AND convalidated
          AND position('version' in lower(pg_get_constraintdef(oid))) > 0
          AND position('> 0' in lower(pg_get_constraintdef(oid))) > 0
    ) THEN
        RAISE EXCEPTION 'SignedChange version CHECK is missing or weakened';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid
          AND conname = 'gerchain_authorization_payload_hash_check'
          AND contype = 'c'
          AND convalidated
          AND position('payload_hash' in lower(pg_get_constraintdef(oid))) > 0
          AND position('^[0-9a-f]{64}' in lower(pg_get_constraintdef(oid))) > 0
    ) THEN
        RAISE EXCEPTION 'SignedChange payload-hash CHECK is missing or weakened';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = table_oid
          AND conname = 'gerchain_authorization_signature_check'
          AND contype = 'c'
          AND convalidated
          AND position('length(signature)' in lower(pg_get_constraintdef(oid))) > 0
          AND position('> 0' in lower(pg_get_constraintdef(oid))) > 0
    ) THEN
        RAISE EXCEPTION 'SignedChange signature CHECK is missing or weakened';
    END IF;
END
$$;

ALTER TABLE gerchain_authorization_changes
    ALTER COLUMN created_at SET DEFAULT now();
