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
| EV-ESC-001 | GC-ESC-001, GC-ESC-002, GC-ESC-003 | SRC | CORE escrow/release implementation — exact path to be indexed | PENDING | CORE | identify authoritative implementation at frozen SHA |
| EV-WIT-001 | GC-WIT-001 | SRC/TEST | witness/verifier implementation and tests — exact path to be indexed | PENDING | CORE | identify source and test artifacts |
| EV-PG-001 | GC-ESC-003, GC-RES-001 | SRC/TEST/CI | PostgreSQL release authority and concurrency/recovery artifacts — exact path to be indexed | PENDING | CORE | inspect atomicity, replay and crash evidence |
| EV-MNY-001 | GC-MNY-001, GC-MNY-002 | SRC/TEST | Money Ledger/Engine — exact path to be indexed | PENDING | CORE | trace single authoritative ownership |
| EV-HLD-001 | GC-HLD-001 | SRC/TEST | Hold Engine — exact path to be indexed | PENDING | CORE | inspect reservation invariants |
| EV-LIM-001 | GC-LIM-001 | SRC/TEST | Limit Engine — exact path to be indexed | PENDING | CORE | inspect limit enforcement |
| EV-TXN-001 | GC-TXN-001 | SRC/TEST | Transaction State Machine — exact path to be indexed | PENDING | CORE | inspect legal transitions |
| EV-SEC-001 | GC-SEC-001 | CFG/LOG | IAM, privileged access, access review, MFA evidence — external evidence required | MISSING | Security | obtain operating-period evidence |
| EV-SEC-002 | GC-SEC-002 | CI | CI/security/dependency evidence — exact runs to be indexed | PENDING | SDLC | map workflows to controls |
| EV-DATA-001 | GC-DATA-001 | TEST/DB | reconciliation, migration, completeness/accuracy evidence — exact artifact required | MISSING | Data | define reproducible population test |
| EV-RES-001 | GC-RES-001 | TEST/REP | crash/recovery/replay re-performance — exact artifact required | MISSING | CORE/DB | execute and retain evidence |
| EV-AUD-001 | GC-AUD-001 | LOG/DB | witness/event/outbox/audit records — exact artifact required | MISSING | Audit | produce sample and full-population evidence |
| EV-CHG-001 | GC-CHG-001 | CI/DOC | audited SHA + corresponding green CI + approval record | PENDING | SDLC | bind evidence to exact baseline |

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

1. Exact authoritative CORE implementation paths for money, escrow, witness, verifier and PostgreSQL release authority.
2. Exact automated test and CI evidence linked to the frozen SHA.
3. Operating-period database/reconciliation evidence.
4. Access-control and privileged-operation evidence.
5. Independent re-performance package.

**Rule:** `PENDING` means the control may exist but the audit evidence has not yet been indexed. `MISSING` means the required evidence artifact is not yet established. Neither may be represented as audited PASS.
