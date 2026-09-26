# PRODUCTION READY — MASTER WORK PLAN v1.0

## Governing Principle

**Production readiness is the governing objective and principle of the work, not a final label applied after implementation.**

Every implementation decision MUST be evaluated against one question:

> Does this change move the fundamental architecture and EAI toward independently verifiable production readiness without creating a second authority, bypass, duplicate truth, or unbounded recovery path?

The objective is therefore:

**BUILD → VERIFY → RECONCILE → INDEPENDENTLY RE-PERFORM → LOCK**

not:

**BUILD → ASSUME READY**

## Scope

The current production-readiness target is:

1. Fundamental architecture / ҮНДСЭН БҮТЭЦ
2. EAI — ESCROW AS INFRASTRUCTURE
3. Canonical value-truth, condition, authority, execution, evidence, recovery and audit boundaries required by EAI.

Product/application layers are outside this gate.

## Non-Negotiable Production Principles

1. One authoritative truth per domain.
2. One authoritative value-movement boundary.
3. No downstream mutation of protected authority.
4. Decision → Authorization → Release is mandatory.
5. Unknown or unresolved required conditions never pass.
6. Every value movement is atomically bound to durable state, witness, outbox and idempotency evidence.
7. Recovery must not create duplicate value movement.
8. Balance equality is insufficient; value-truth equality must be reconciled through movement identity and evidence.
9. Production must fail closed when canonical authority is unavailable.
10. Legacy authorities may not silently become fallback authorities.
11. Schema readiness must be proven on real PostgreSQL, not inferred from SQLite or create_all alone.
12. A production claim requires fresh, reproducible evidence tied to an exact commit.

## Master Gate

No production lock until all are independently evidenced:

CANONICAL ARCHITECTURE
→ AUTHORITY MAP
→ CANONICAL VALUE FLOW
→ DURABLE ESCROW
→ EAI CONDITIONS
→ ATOMIC TRANSACTION
→ WITNESS
→ OUTBOX
→ IDEMPOTENCY
→ RECOVERY
→ DEEP VALUE-TRUTH RECONCILIATION
→ SECURITY / IAM
→ OBSERVABILITY
→ PERFORMANCE / STRESS
→ DISASTER RECOVERY
→ CI / RELEASE
→ INDEPENDENT RE-PERFORMANCE
→ FINAL EVIDENCE
→ PRODUCTION LOCK

## Current Gate

EA-35: **IN PROGRESS / NOT LOCKED**

Current verified implementation direction:

- Production entrypoint requires PostgreSQL.
- ProductionRuntimeFactory constructs the canonical runtime.
- Versioned PostgreSQL migrations are applied during production construction.
- Canonical production schema is checked explicitly before runtime authority is accepted.
- Runtime authority is attached through the Canonical Ledger boundary.
- Deep value-truth reconciliation is implemented with negative-path tests.

Still required before lock:

- actual PostgreSQL execution evidence at the exact branch tip;
- full lifecycle re-performance;
- recovery/restart evidence;
- CI evidence;
- independent re-performance;
- final evidence index and lock record.

## Evidence Rule

**No evidence = no claim.**

A test that has not actually executed is UNVERIFIED.
A static inspection is implementation evidence, not runtime evidence.
A local test is not automatically production evidence.
A CI result must identify the exact commit SHA and job.
A production PostgreSQL result must identify database engine/version, migration state, test scope and outcome.

## Lock Rule

Only after every mandatory gate has fresh evidence may the architecture be marked:

**PRODUCTION READY — LOCKED**
