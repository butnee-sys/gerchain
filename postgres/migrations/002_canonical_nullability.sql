-- Canonical production nullability hardening, migration 002.
-- Migration 001 intentionally remains immutable for checksum integrity.

ALTER TABLE escrows
    ALTER COLUMN refund_destination SET NOT NULL,
    ALTER COLUMN currency SET NOT NULL;

ALTER TABLE gerchain_ledger_movements
    ALTER COLUMN integrity_hash SET NOT NULL;
