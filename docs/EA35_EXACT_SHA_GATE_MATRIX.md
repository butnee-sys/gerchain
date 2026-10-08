# EA-35 Exact-SHA Gate Matrix

Status: IN PROGRESS / NOT LOCKED

## Gate rule

A gate is SUCCESS only when execution evidence exists for the exact branch SHA under review.
A QUEUED, missing, stale, default-branch, or inferred result is not SUCCESS.

## Current exact-SHA target

Branch: feat/ea21-transaction-aware-ledger
Latest explicitly verified implementation SHA in this workstream:
e860f502f3e1a2d56fd873ad2faab7b1ab630740

## Matrix

| Gate | Required evidence | Status |
|---|---|---|
| EA-35.1 deep reconciliation implementation | exact-SHA source inspection | SUCCESS |
| EA-35.2 clean graph | exact-SHA test implementation | SUCCESS |
| EA-35.3 movement integrity binding | exact-SHA source + negative test implementation | SUCCESS |
| EA-35.4 rollback atomicity | exact-SHA test implementation | SUCCESS |
| EA-35.5 replay/idempotency | exact-SHA test implementation | SUCCESS |
| EA-35.6 LOCK state-only separation | exact-SHA test implementation | SUCCESS |
| EA-35.7 outbox operation binding | exact-SHA source + negative test implementation | SUCCESS |
| EA-35.8 stale idempotency false-positive removal | exact-SHA source + test implementation | SUCCESS |
| EA-35.9 production PostgreSQL execution | actual run result on exact SHA | QUEUED |
| EA-35.10 production entrypoint boot | actual PostgreSQL boot result on exact SHA | QUEUED |
| EA-35.11 schema completeness | actual PostgreSQL migration/boot evidence | QUEUED |
| EA-35.12 deep reconciliation on PostgreSQL | actual PostgreSQL execution result | QUEUED |
| EA-35.13 recovery/restart | actual execution evidence | QUEUED |
| EA-35.14 CI exact-SHA | successful workflow/check for exact SHA | QUEUED |
| EA-35.15 independent re-performance | independent execution/evidence | QUEUED |

## Lock invariant

EA-35 MUST NOT be declared LOCKED while any required gate remains QUEUED, UNVERIFIED, FAILED, or OPEN.

## Evidence integrity

Implementation inspection is not equivalent to runtime execution.
A test file existing is not equivalent to a successful test run.
A historical green result from another SHA is not evidence for the current SHA.

Therefore the remaining QUEUED gates require fresh execution evidence before the EA-35 LOCK evidence and LOCK commit can be created.
