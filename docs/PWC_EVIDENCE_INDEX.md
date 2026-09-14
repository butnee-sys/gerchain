# PwC-Style Core Evidence Index

**Scope:** DE / DEE / G-3 / NEF / GerChain CORE / EXIM / I2B only.

**SHUUD:** explicitly excluded.

**Audit baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`

## Evidence collection rule

Each row must eventually point to an exact, reproducible artifact. Use the following classes:

- `SRC` — source code
- `TEST` — automated test
- `CI` — CI/workflow result
- `DB` — database execution/reconciliation evidence
- `LOG` — execution/audit log
- `CFG` — configuration/access evidence
- `DOC` — governance/design document
- `REP` — independent re-performance

| Evidence ID | Control IDs | Evidence class | Exact location / artifact | Status | Owner | Auditor action |
|---|---|---|---|---|---|---|
| EV-ARCH-001 | GC-ARCH-001, GC-ARCH-002 | DOC | `docs/CORE_FREEZE_RECORD.md` | FOUND | Architecture | inspect exact baseline and lock rule |
| EV-ARCH-002 | GC-ARCH-001, GC-BOUND-001 | SRC | `architecture/governed_flow_adapters.py` | FOUND | Architecture | inspect adapter contract and fail-closed behavior |
| EV-ARCH-003 | GC-BOUND-002, GC-BOUND-003, GC-I2B-001 | SRC | `architecture/ports.py` | FOUND | Architecture | trace ports and actor routing |
| EV-NEF-001 | GC-NEF-001, GC-NEF-002 | SRC | `architecture/nef_gerchain.py` | FOUND | NEF | re-perform validation and boundary assertions |
| EV-MNY-001 | GC-MNY-001 | SRC | `money/ledger.py` | FOUND | CORE | inspect single authoritative ledger ownership |
| EV-MNY-002 | GC-MNY-002 | SRC | `money/engine.py` | FOUND | CORE | trace authorized value movement into ledger |
| EV-ESC-001 | GC-ESC-001 | SRC | `escrow/state.py` | FOUND | CORE | inspect legal escrow state transitions |
| EV-ESC-002 | GC-ESC-002 | SRC | `escrow/engine.py` | FOUND | CORE | inspect escrow lifecycle authority |
| EV-ESC-003 | GC-ESC-003 | SRC/TEST | `persistence/atomic_release.py`; `tests/test_authoritative_fund_atomicity.py` | FOUND + TEST | CORE | re-perform atomic release and rollback invariants |
| EV-IDM-001 | GC-IDM-001 | SRC/TEST | `persistence/atomic_release.py`; `tests/test_authoritative_release_idempotency.py` | FOUND + TEST | CORE | re-perform replay and same-key conflict behavior |
| EV-WIT-001 | GC-WIT-001 | SRC | `witness/chain.py` | FOUND | CORE | inspect witness-chain integrity and append authority |
| EV-WIT-002 | GC-WIT-002 | SRC | `witness/independent_multi.py` | FOUND | CORE | inspect independent witness verification path |
| EV-PG-001 | GC-ESC-003, GC-RES-001 | SRC | `persistence/atomic_release.py` | FOUND | CORE/DB | inspect transaction boundary, row locks and commit/rollback behavior |
| EV-PG-002 | GC-RES-001 | DOC | `docs/POSTGRES_ATOMIC_RELEASE.md` | FOUND | CORE/DB | verify documented PostgreSQL atomic boundary |
| EV-PG-003 | GC-IDM-001, GC-RES-001 | DOC | `docs/POSTGRES_IDEMPOTENCY.md` | FOUND | CORE/DB | verify idempotency and transaction-boundary requirements |
| EV-PG-004 | GC-RES-002 | SRC | `persistence/recovery_outbox.py` | FOUND | CORE/DB | inspect lease, claim, heartbeat and completion controls |
| EV-PG-005 | GC-RES-001, GC-RES-002 | DOC/TEST | `docs/GATE_05_CRASH_RECOVERY.md`; `tests/test_release_crash_recovery_contract.py` | FOUND + TEST | CORE/DB | re-perform replay and expired-outbox recovery |
| EV-PG-006 | GC-RES-001, GC-RES-002 | TEST | `tests/test_release_crash_recovery_contract.py` | FOUND | CORE/DB | execute against PostgreSQL test database and retain result |
| EV-PG-007 | GC-RES-002 | DOC | `docs/POSTGRES_RECOVERY_OUTBOX.md` | FOUND | CORE/DB | inspect recovery contract and at-least-once boundary |
| EV-PG-008 | GC-RES-003 | DOC | `docs/RELEASE_FAILURE_RECOVERY_CONTRACT.md` | FOUND | CORE/DB | verify failure-state contract |
| EV-PG-009 | GC-IDM-002, GC-RES-003 | DOC | `docs/GATE_04_IDEMPOTENCY_CONCURRENCY.md` | FOUND | CORE/DB | inspect concurrency/idempotency invariants |
| EV-HLD-001 | GC-HLD-001 | SRC | `core/hold.py` | FOUND | CORE | inspect hold/reservation invariants |
| EV-LIM-001 | GC-LIM-001 | SRC | `core/limit.py` | FOUND | CORE | inspect limit enforcement |
| EV-TXN-001 | GC-TXN-001 | SRC | `core/transaction_lifecycle.py` | FOUND | CORE | inspect legal transaction transitions |
| EV-RES-001 | GC-RES-001 | TEST/REP | PostgreSQL execution and independent crash/recovery re-performance package | MISSING | CORE/DB | execute on controlled PostgreSQL environment and retain raw evidence |
| EV-RES-002 | GC-RES-003 | TEST/DB | Abandoned `ReleaseOperation` in `PROCESSING` recovery/lease policy | MISSING | CORE/DB | implement or formally evidence recovery before audit assertion |
| EV-SEC-001 | GC-SEC-001 | CFG/LOG | IAM, privileged access, access review, MFA evidence — external evidence required | MISSING | Security | obtain operating-period evidence |
| EV-SEC-002 | GC-SEC-002 | CI | CI/security/dependency evidence — exact runs to be indexed | PENDING | SDLC | map workflows to controls and frozen-SHA results |
| EV-DATA-001 | GC-DATA-001 | TEST/DB | reconciliation, migration, completeness/accuracy evidence — exact artifact required | MISSING | Data | define reproducible population test |
| EV-AUD-001 | GC-AUD-001 | LOG/DB | witness/event/outbox/audit records — exact artifact required | MISSING | Audit | produce sample and full-population evidence |
| EV-CHG-001 | GC-CHG-001 | CI/DOC | audited SHA + corresponding green CI + approval record | PENDING | SDLC | bind evidence to exact baseline and approval |
| EV-IND-001 | GC-IND-001 | REP | independent re-performance by auditor/independent reviewer | MISSING | Independent Assurance | execute using clean environment and preserve result |

## Audit-status interpretation

`FOUND` means the repository contains the referenced artifact. `FOUND + TEST` means a corresponding automated test artifact is also indexed. Neither status means the control is independently assured or operating effectively.

A control should progress through: `DESIGNED → IMPLEMENTED → TESTED → EVIDENCED → OPERATING EFFECTIVE → INDEPENDENTLY ASSURED`.

## Auditor evidence packet requirements

For every critical control, retain:

1. control statement;
2. exact implementation path;
3. exact commit SHA;
4. test name(s);
5. test result;
6. representative execution evidence;
7. failure/recovery evidence where relevant;
8. owner and reviewer;
9. date/time and environment;
10. independent re-performance result.

## Evidence gaps to close first

1. Execute the indexed PostgreSQL atomic-release/recovery tests against a controlled database and retain raw run evidence.
2. Resolve the abandoned `ReleaseOperation` `PROCESSING` recovery/lease gap.
3. Produce operating-period database/reconciliation evidence.
4. Produce IAM, privileged-access and MFA evidence.
5. Bind green CI results and approval evidence to the exact audit baseline.
6. Complete independent re-performance.

**Rule:** `PENDING` means the control may exist but the audit evidence has not yet been indexed. `MISSING` means the required evidence artifact is not yet established. Neither may be represented as audited PASS.
