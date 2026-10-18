# FINAL LOCK ADDENDUM — EAI / Canonical Production Runtime

**Status:** ADDENDUM RECORDED — PRODUCTION NOT LOCKED  
**Date:** 2026-10-18  
**Repository:** `butnee-sys/gerchain`  
**Working branch:** `feat/ea21-transaction-aware-ledger`  
**Relevant implementation commit:** `e860f502f3e1a2d56fd873ad2faab7b1ab630740`

## Purpose

This addendum records the production-runtime correction for Escrow as Infrastructure (EAI) against the existing frozen canonical architecture. It does not rewrite, supersede, or silently mutate the frozen architecture document or any previously accepted FINAL LOCK record.

## Architecture preservation

- EAI means **Escrow as Infrastructure**; it is an architectural principle, not a new canonical layer, a second Escrow Engine, or a second authoritative Ledger/Witness chain.
- The canonical production value authority remains `gerchain_ledger_accounts` and `gerchain_ledger_movements`, through the transaction-aware `PostgreSQLAtomicLedger` boundary.
- Production runtime construction must configure and require Canonical Ledger authority; it must not silently initialize legacy `AtomicRelease` as the production authority.
- Existing frozen canonical architecture remains unchanged. This addendum is an evidence/change record only.

## Correction recorded

The production entrypoint previously called `ProductionRuntimeFactory.create(...)` as though it were a class-level constructor, although the repository factory exposes an instance method with a `ProductionRuntimeConfig`. The factory also initialized the legacy Atomic Release persistence and configured PostgreSQL release authority, while the entrypoint asserted Canonical Ledger authority.

Commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` updates the entrypoint to construct `ProductionRuntimeConfig`, instantiate `ProductionRuntimeFactory`, and call `factory.create()`. The factory initializes canonical persistence metadata and calls `configure_canonical_ledger()` followed by `require_canonical_ledger_authority()`.

## Evidence boundary

This commit is evidence of a **source correction only**. It is not evidence of a successful production boot or a completed production migration. The following remain required before EAI / the overall fundamental infrastructure can be declared production-ready and locked:

1. Validate the factory and entrypoint against the exact branch commit.
2. Apply and verify explicit PostgreSQL schema migrations; `metadata.create_all()` is not a substitute for migration management.
3. Boot against a real PostgreSQL instance and retain logs/results tied to the exact commit SHA.
4. Exercise CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT and READ against the same canonical durable truth.
5. Run deep value-truth reconciliation and verify movement, escrow, witness, outbox, idempotency and integrity bindings.
6. Test restart, failure recovery, idempotent replay and conflict behavior.
7. Obtain successful exact-SHA CI and independent re-performance evidence.
8. Resolve production entrypoint readiness/health semantics and any remaining schema or runtime defects.

## Lock rule

**The prior FINAL LOCK is not silently reopened or rewritten.** This addendum appends the production-runtime correction to its evidence trail. It does **not** promote EAI, the fundamental architecture, or the current branch to production-ready. Until all required evidence above is retained and reviewed, the status remains:

**EAI / FUNDAMENTAL PRODUCTION INFRASTRUCTURE: IN PROGRESS / NOT LOCKED.**

No product-layer work is implied or authorized by this addendum.
