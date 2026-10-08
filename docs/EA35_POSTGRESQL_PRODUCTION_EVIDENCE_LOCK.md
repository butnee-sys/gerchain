# EA-35 PostgreSQL Production Evidence Lock

Status: LOCKED — PostgreSQL production/re-performance gate
Locked commit: 8398c76127b79b0b442dc8a987a854f2215d8fde
Date: 2026-10-08

## Scope

This lock covers the EA-35 PostgreSQL production evidence gate for the current canonical value-flow implementation.

It does NOT by itself lock the whole EAI, whole CORE, or the entire production architecture.

## Evidence

The branch `feat/ea21-transaction-aware-ledger` points to commit `8398c76127b79b0b442dc8a987a854f2215d8fde`.

Fresh GitHub Actions runs for this exact commit completed successfully:

- Production PostgreSQL Re-performance: run 37746458704 — success
- independent-postgresql-evidence: run 37746458433 — success
- EA-35 PostgreSQL production smoke: run 37746453282 — success

Production PostgreSQL Re-performance job completed both:
1. Production PostgreSQL boot
2. Deep value truth PostgreSQL re-performance

Independent evidence completed:
1. Independent persisted-value verification

The production smoke completed the PostgreSQL production lifecycle test suite.

## Locked conclusions

1. PostgreSQL is the tested production persistence authority for this gate.
2. Production runtime construction establishes Canonical Ledger authority.
3. Canonical PostgreSQL schema migration and required-schema assertion are part of runtime construction.
4. PostgreSQL production boot has fresh successful CI evidence.
5. Deep value-truth reconciliation has fresh successful PostgreSQL evidence.
6. Independent persisted-value verification has fresh successful evidence.
7. Replay/idempotency and protected refund-destination behavior are included in the production smoke path.
8. No claim is made here that the entire EAI or entire production architecture is locked.

## Non-negotiable

Any change to canonical value authority, PostgreSQL migration history, production runtime construction, transaction-aware Ledger boundary, Escrow aggregate boundary, Witness, Outbox, Idempotency, or deep value-truth reconciliation invalidates this evidence lock and requires re-performance.

CI success is repository technical evidence, not external certification or regulatory attestation.
