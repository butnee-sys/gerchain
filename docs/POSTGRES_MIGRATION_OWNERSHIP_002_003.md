# Canonical PostgreSQL Migration Ownership: Versions 002–003

Status: migration ownership clarification; this document does not rewrite any published migration.
Applies to: `postgres/migrations/` only. The older `postgres/schema/` directory is a legacy/reference collection and is not the active numbered migration chain.

## Canonical execution order

The production runner selects exactly one file for each version 001–017 from `postgres/migrations/`, verifies the source checksum against `schema_version`, and applies versions in ascending order. A same-version file in `postgres/schema/` is not an additional migration and must never be executed as part of the active chain.

| Version | File | Ownership |
|---|---|---|
| 001 | `001_canonical_production.sql` | Initial schema bootstrap. Its historical state CHECK is provisional and may be normalized by later migrations. |
| 002 | `002_canonical_production.sql` | Canonical persistence bootstrap/compatibility upgrade: escrow columns and base tables for Ledger, movement evidence, Witness, Idempotency and Outbox. It contains historical state-CHECK normalization; it is not the final owner of the escrow-state invariant. |
| 003 | `003_canonical_compatibility.sql` | Index-only compatibility/performance migration for Ledger movement, Witness, and Outbox aggregate lookups. It must not create, drop, or redefine an escrow state CHECK. |
| 005 | `005_canonical_production.sql` | Historical lifecycle hardening step. It normalizes state CHECK constraints for databases that reached this point before the later canonical naming repair. |
| 014 | `014_canonical_escrow_state_constraint.sql` | Introduces the named canonical state constraint, `escrows_state_canonical_check`, while retiring known stale names. |
| 015 | `015_repair_escrow_state_constraint_drift.sql` | Repairs any state-related CHECK drift and validates the canonical constraint. |
| 016 | `016_reconcile_escrow_state_constraint.sql` | Final reconciliation owner: removes every competing CHECK involving `escrows.state`, recreates and validates exactly one `escrows_state_canonical_check`. |

## Resolution of the 002/003 overlap

1. Version 002 is the persistence-schema owner; version 003 is index-only. Version 003 does not own escrow lifecycle semantics.
2. Version 002 has a repeated `DROP CONSTRAINT IF EXISTS escrows_state_check` statement. The repeated drop is a redundant no-op in that historical migration, not a second migration version. Do not edit the published file because its checksum is part of migration history.
3. The lifecycle CHECK in 002 is transitional. Versions 014–016 are the canonical constraint-repair sequence, with version 016 responsible for the final invariant: exactly one validated `escrows_state_canonical_check` allowing CREATED, FUNDED, LOCKED, RELEASED, REFUNDED, CANCELLED.
4. Do not execute SQL from `postgres/schema/` in addition to `postgres/migrations/`. That directory contains legacy alternatives and repeated numeric prefixes; the active migration manifest is the sole execution authority.
5. A successful fresh-database migration is necessary but not sufficient: also verify replay/idempotency, schema catalog invariants, legacy upgrade preservation, production runtime boot, full lifecycle, and deep value-truth reconciliation on the same commit SHA.

## Evidence binding

The release evidence must record the exact Git commit SHA, migration file SHA-256 for every selected version, runner checksum for every selected version, PostgreSQL major version, ordered `schema_version` rows, second-run no-op result, catalog verification result, workflow run ID/attempt, and the resulting artifact URL. A result from another commit is historical evidence only.

This clarification does not declare EAI or the production architecture locked. Production lock remains blocked until every required gate and evidence artifact passes on the same commit.
