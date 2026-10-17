# EA-35 Final Evidence Manifest — Candidate, Not Locked

**Repository:** `butnee-sys/gerchain`  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Evidence snapshot SHA:** `e85c98407432cace92c30f8f55a7ee9c1917d1f9`  
**Snapshot date:** 2026-10-09  
**Decision:** **FINAL LOCK BLOCKED — NOT PRODUCTION-LOCKED**

This manifest consolidates the evidence available at the exact snapshot SHA. It is deliberately not a production certificate. A queued check is not a pass, a security-only status is not a runtime pass, and source inspection is not proof of a successful PostgreSQL execution.

## 1. Architecture and authority invariants

- Canonical architecture freeze remains the controlling architecture document; implementation changes require explicit approved architecture change.
- Production value authority is the Canonical Ledger: `gerchain_ledger_accounts` and `gerchain_ledger_movements`.
- Production value mutations must pass through the transaction-aware Canonical Ledger boundary.
- Escrow state, value movement, witness, idempotency, and transactional outbox evidence must reconcile as one transaction truth.
- Unknown or unresolved required conditions fail closed.
- No direct Release, duplicate authoritative Ledger, duplicate Witness Chain, or application-owned production balance mutation is permitted.
- `Balance equality ≠ Value-truth equality.`

## 2. Evidence snapshot

| Gate | Evidence observed | Status |
|---|---|---|
| Exact branch SHA | GitHub branch ref resolves to `e85c98407432cace92c30f8f55a7ee9c1917d1f9` | VERIFIED |
| Security status | Snyk status on exact SHA: “2 security tests have passed” | PASS — security only |
| GitHub Actions | Exact-SHA check-runs include PostgreSQL production runtime, EA-35 PostgreSQL gate, smoke, full suite, reconciliation, and independent PostgreSQL evidence checks; observed state was queued/pending | **UNVERIFIED** |
| PostgreSQL runtime factory | Source calls canonical runtime configuration and schema migration/validation | IMPLEMENTED; runtime execution pending |
| Production entrypoint | Source validates PostgreSQL DSN and required environment; builds factory instance; fails if Canonical Ledger authority is absent | IMPLEMENTED; runtime execution pending |
| Migration history | Migration runner requires schema version 13; migration directory contains numbered migration files through 013 | SOURCE-INSPECTED; successful fresh and upgrade paths pending |
| Deep value reconciliation | Implementation and unit/integration test source exist | SOURCE-INSPECTED; exact-SHA execution pending |
| Independent re-performance | No completed independent report identified in this snapshot | OPEN |
| Production IAM/MFA and privileged-access evidence | Previously recorded as missing in the audit register; no new closure evidence identified here | OPEN |
| Main-branch governance / merge | PR #90 remains open; feature branch is not the main branch | OPEN |

## 3. Required closure conditions

FINAL LOCK is allowed only after all conditions below have exact-SHA evidence:

1. All required GitHub Actions checks complete successfully on the same commit SHA; no queued, skipped, cancelled, or missing required check is accepted as PASS.
2. Fresh PostgreSQL 16 CI proves clean-database migration, repeat migration, upgrade/compatibility behavior, runtime boot, canonical CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ paths, idempotent replay, conflict rejection, and rollback.
3. Deep value-truth reconciliation returns matched for the exercised graph and negative cases detect every seeded mismatch.
4. Restart/recovery testing proves no duplicate value movement and no alternate truth authority.
5. Migration publication concurrency test passes on the exact SHA.
6. Existing production data is explicitly reconciled/backfilled; migration must fail closed where required currency or refund destination is unknown.
7. IAM/MFA, privileged-access review, independent re-performance, and governance evidence are either completed or formally accepted by the designated authority with scope and expiry.
8. Legacy value stores and direct mutation paths are demonstrably read-only/non-authoritative in production.
9. PR review/merge and protected-main checks satisfy the repository's release policy.
10. Final manifest is regenerated from the final passing SHA; any code change invalidates prior exact-SHA test evidence.

## 4. Decision rule

- **PASS:** fresh, complete, exact-SHA evidence exists and the requirement is satisfied.
- **OPEN:** evidence or implementation is incomplete.
- **UNVERIFIED:** evidence is absent, stale, queued, cancelled, or not tied to the exact SHA.
- **BLOCKED:** a required condition prevents production lock.

No overall GREEN status may be inferred from partial successes. At this snapshot, FINAL LOCK remains **BLOCKED** by pending exact-SHA CI and open independent/governance evidence.
