# EAI — PRODUCTION GATE EVIDENCE

Status: VERIFIED / NOT LOCKED

## Scope

EAI (Escrow as Infrastructure) is an architectural principle implemented through the frozen architecture, G3 Escrow Foundation, Canonical Escrow state, Canonical Ledger value authority, Witness, Outbox, Idempotency, and Recovery boundaries.

EAI is not a new canonical architecture layer and does not create a second Escrow Engine or second authoritative value truth.

## Evidence already executed

Exact PostgreSQL 16 GitHub Actions evidence on execution SHA `890a78f36dcfe161e195da649b3cd124133d6535`:

- PostgreSQL production re-performance — run `36317914217` — success
- Production PostgreSQL Runtime — run `36317914351` — success
- PostgreSQL smoke — run `36317914313` — success
- PostgreSQL canonical proof — run `36317914446` — success
- PostgreSQL production gate — run `36317914344` — success
- PostgreSQL production verification — run `36317914254` — success
- EAI PostgreSQL re-performance — run `36317914266` — success

Observed test evidence includes canonical production runtime establishment, PostgreSQL production integration, restart/replay semantics, deep value-truth reconciliation, EAI PostgreSQL re-performance, and canonical schema/runtime proof.

Representative exact outputs included `canonical production runtime: OK`, `1 passed`, `2 passed`, and `19 passed` for the relevant proof jobs.

## Current release boundary

The later production-factory correction commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` changes production construction from the legacy PostgreSQL release configuration to the Canonical Ledger configuration and corrects the entrypoint to instantiate `ProductionRuntimeFactory` with `ProductionRuntimeConfig`.

This correction is implemented but its exact-SHA PostgreSQL re-performance evidence has not yet been independently retrieved. Therefore the earlier successful evidence must not be relabeled as evidence for the later SHA.

## Lock blockers

1. Exact-SHA PostgreSQL re-performance for the current release tip.
2. Final independent re-performance/oracle package.
3. Physical legacy-store removal/archive closure.
4. IAM/MFA and privileged-access assurance closure.
5. Branch/main governance closure.

## Hard invariant

**ONE ESCROW AGGREGATE → ONE CANONICAL ESCROW STATE MACHINE → ONE DURABLE ESCROW TRUTH → ONE AUTHORITATIVE VALUE-MOVEMENT BOUNDARY → ONE WITNESS PATH → ONE OUTBOX PATH → ONE RECOVERY PATH**

No production lock is declared until every blocker above is evidenced and reviewed.