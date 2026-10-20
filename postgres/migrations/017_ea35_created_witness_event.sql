-- EA-35.14: permit canonical state-only CREATE witness evidence.
-- Version 17. GERCHAIN_CREATED is a state/evidence event, not a value movement.
-- Preserve all prior migration files and checksums; update the constraint additively.
ALTER TABLE gerchain_transaction_witnesses
    DROP CONSTRAINT IF EXISTS gerchain_witness_event_type_check;

ALTER TABLE gerchain_transaction_witnesses
    ADD CONSTRAINT gerchain_witness_event_type_check CHECK (
        event_type IN (
            'GERCHAIN_CREATED',
            'GERCHAIN_FUNDED',
            'GERCHAIN_LOCKED',
            'GERCHAIN_RELEASED',
            'GERCHAIN_REFUNDED',
            'GERCHAIN_CANCELLED',
            'GERCHAIN_SETTLED'
        )
    );
