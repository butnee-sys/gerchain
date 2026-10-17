# FINAL LOCK RECORD — Fundamental Architecture + EAI

**Status: FINAL LOCK IN PROGRESS — NOT LOCKED**  
**Record initiated:** 2026-10-09  
**Repository:** `butnee-sys/gerchain`  
**Working branch:** `feat/ea21-transaction-aware-ledger`  
**Scope:** Fundamental/canonical architecture and EAI (Escrow as Infrastructure). Product layers are explicitly excluded.

## 1. Lock decision rule

This record does not declare a lock merely because implementation code exists or a historical workflow passed. Final lock requires:
1. an immutable exact commit SHA under review;
2. fresh successful required CI and PostgreSQL production evidence tied to that SHA;
3. no unresolved critical architecture/value-authority bypass;
4. explicit reconciliation of legacy value stores and migration state;
5. independent re-performance evidence;
6. IAM/MFA and privileged-access assurance, or a formally approved and scoped audit exception;
7. verified main-branch governance / protection evidence;
8. a final evidence index and control matrix consistent with the exact audited SHA.

Unknown, missing, stale, or unverified evidence is not PASS.

## 2. Canonical invariants to preserve

- One authoritative Canonical Ledger for production balances and value movements.
- One durable Canonical Escrow state machine.
- One authoritative Witness path and one production Outbox path.
- Decision → Authorization → Release is mandatory.
- No direct release or application-owned value mutation.
- No duplicate Escrow Engine, Ledger, or Witness Chain authority.
- Escrow state, Ledger movement, witness, idempotency, and outbox evidence must reconcile.
- Same idempotency key and same request replays safely; same key with a different fingerprint conflicts.
- Recovery cannot duplicate value movement.
- Unresolved required conditions fail closed.
- EAI is an architectural principle, not a new architecture layer or a second escrow engine.
- CORE is one infrastructure/sub-infrastructure; this lock scope is the fundamental architecture plus EAI, not CORE alone.
- PDEIZ is a protective-zone concept over NEF + G3 + GerChain, not a new canonical layer.
- SHUUD/SHIID and other product layers are out of scope until the fundamental architecture and EAI are fully locked.

## 3. Evidence currently recorded

The repository audit document `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md` records that on 2026-10-06, exact-branch production PostgreSQL workflows passed for commit `f11fcb6411f1458c7bb4696566a695a52141b0c3`, including production PostgreSQL, production gate, EAI PostgreSQL proof, independent persisted-value verification, CORE operating reconciliation, and CodeQL.

That is historical evidence for that exact commit. It is not, by itself, proof that the current branch tip has the same evidence. The available combined-status query for that SHA exposed only the Snyk success status; the recorded workflow runs must be rechecked against the current exact SHA before final lock.

## 4. Final-lock gate matrix

| Gate | Current status | Closure evidence required |
|---|---|---|
| Canonical architecture invariants | BASELINED | Freeze document and exact-SHA conformance review |
| Production PostgreSQL runtime / EAI | HISTORICAL PASS; CURRENT SHA UNVERIFIED | Fresh successful workflow runs tied to exact reviewed SHA |
| Canonical value-flow lifecycle | HISTORICAL PASS; CURRENT SHA UNVERIFIED | PostgreSQL CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ proof |
| Deep Value Truth Reconciliation | HISTORICAL PASS; CURRENT SHA UNVERIFIED | Clean graph plus negative mismatch tests on exact SHA |
| Legacy value-store authority | OPEN | Read-only/frozen status proven; reconcile then archive/remove duplicate authorities safely |
| Schema/migration completeness | OPEN UNTIL VERIFIED ON CURRENT SHA | Migration history and required schema assertions pass on a clean PostgreSQL instance and supported upgrade path |
| Runtime/entrypoint correctness | IMPLEMENTED; CURRENT SHA UNVERIFIED | Entrypoint boot and fail-closed tests on PostgreSQL |
| Independent re-performance | HISTORICAL EVIDENCE RECORDED; CURRENT SHA UNVERIFIED | Independent job/artifact and exact-SHA binding verified |
| IAM/MFA and privileged-access review | MISSING / OPEN | Organizational evidence or formally approved audit exception |
| Main-branch protection/governance | MISSING / UNVERIFIED | Actual protection/ruleset/review settings verified |
| Evidence index/control matrix | OPEN | All rows, dates, run URLs and SHAs consistent |
| Final architecture/oracle package | OPEN | Independent architecture review, invariant-to-test mapping, signed-off evidence package |

## 5. Current disposition

**Do not mark the overall fundamental architecture or EAI FINAL LOCK as complete yet.**

The immediate sequence is:
1. resolve the exact current branch-tip SHA;
2. run/check the required workflows against that SHA;
3. inspect job steps and artifacts for PostgreSQL boot, lifecycle, reconciliation, and independent verification;
4. resolve schema/migration and legacy-authority gates;
5. obtain IAM/MFA and main-branch governance evidence or explicitly approved exceptions;
6. update the evidence index/control matrix;
7. record the final lock decision against an immutable SHA.

Until all mandatory gates are closed or formally excepted by the accountable authority, the truthful state remains **FINAL LOCK IN PROGRESS / NOT LOCKED**.
