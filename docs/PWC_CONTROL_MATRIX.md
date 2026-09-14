# PwC-Style Core Control Matrix

**Scope:** Digital Economy core only. SHUUD is excluded.

**Baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`

| ID | Control objective | Control / owner | Mechanism | Evidence required | Risk addressed | Design | Operating | Independent test |
|---|---|---|---|---|---|---|---|---|
| GC-ARCH-001 | Enforce canonical architecture and ownership | Frozen topology / architecture owners | Layer → Adapter → Layer | freeze record, ports, adapters, architecture test | bypass, duplication, ownership ambiguity | PASS | MISSING | MISSING |
| GC-ARCH-002 | Prevent CORE changes through product work | CORE freeze rule | separate architecture-change cycle | freeze record, branch/PR history | uncontrolled change | PASS | MISSING | MISSING |
| GC-NEF-001 | Accept only valid asset truth into value flow | NEF | explicit `NEFToGerChainAdapter` validation | source, adapter tests, integration execution | invalid/stale asset | PASS | MISSING | MISSING |
| GC-NEF-002 | Preserve asset-truth ownership boundary | NEF | asset reference only; no ledger/escrow implementation | source, architecture tests | duplicated asset/value ownership | PASS | MISSING | MISSING |
| GC-ESC-001 | Release escrow only under valid state/authorization | GerChain CORE | escrow state machine + release authority | source, unit/integration/concurrency tests, DB evidence | unauthorized/duplicate release | PASS | MISSING | MISSING |
| GC-ESC-002 | Prevent duplicate release | GerChain CORE | idempotency + atomic transaction | duplicate-release test, DB record | double spend/release | PASS | MISSING | MISSING |
| GC-ESC-003 | Recover safely after crash/replay | PostgreSQL Release Authority | atomic release + outbox + recovery/replay | crash/replay logs and re-performance | partial release, lost event | PASS | MISSING | MISSING |
| GC-IDM-001 | Guarantee exactly-once value movement for an idempotent release request | PostgreSQL Release Authority | unique idempotency key + row lock + replay/conflict handling | source, idempotency test, DB execution evidence | duplicate value movement | PASS | MISSING | MISSING |
| GC-IDM-002 | Prevent concurrent requests from creating multiple authoritative outcomes | PostgreSQL Release Authority | transactional idempotency/concurrency control | concurrency test, PostgreSQL execution result | race condition/double release | PASS | MISSING | MISSING |
| GC-WIT-001 | Make critical actions attestable through an append-only witness path | Witness / verifier | witness chain + independent verification | witness records, verifier tests | unverifiable action | PASS | MISSING | MISSING |
| GC-WIT-002 | Provide an independent verification path for critical evidence | Witness / verifier | independent multi-witness implementation | verifier source, verification tests, independent re-performance | single-source attestation failure | PASS | MISSING | MISSING |
| GC-MNY-001 | Maintain one authoritative money ledger | GerChain CORE | canonical ledger | source, invariants, reconciliation | inconsistent balances | PASS* | MISSING | MISSING |
| GC-MNY-002 | Enforce money movement invariants | Money Engine | controlled state transition | unit/integration/property tests | invalid value movement | PASS* | MISSING | MISSING |
| GC-HLD-001 | Prevent conflicting reservations | Hold Engine | reservation/hold rules | hold tests, concurrent tests | oversubscription | PASS* | MISSING | MISSING |
| GC-LIM-001 | Enforce transaction limits | Limit Engine | pre-release limit checks | boundary tests, policy evidence | excessive/unauthorized value | PASS* | MISSING | MISSING |
| GC-TXN-001 | Enforce transaction lifecycle | Transaction State Machine | explicit legal states/transitions | transition tests | illegal state mutation | PASS* | MISSING | MISSING |
| GC-BOUND-001 | Fail closed at governed boundaries | Boundary adapters | typed request/response contracts | adapter source and tests | malformed/bypass requests | PASS | MISSING | MISSING |
| GC-BOUND-002 | Prevent CORE internals leaking to external systems | CORE → EXIM | explicit EXIM adapter/port | adapter source, interface tests | coupling/data leakage | PASS | MISSING | MISSING |
| GC-BOUND-003 | Control EXIM ↔ I2B movement | EXIM/I2B boundary | explicit directional adapters | adapter tests, contract evidence | unauthorized external/business path | PASS | MISSING | MISSING |
| GC-I2B-001 | Route business activity only through registered connector | I2B / MultiConnector | actor-type routing, reject missing connector | source, routing tests | ungoverned actor access | PASS | MISSING | MISSING |
| GC-DATA-001 | Preserve data completeness/accuracy | Data control owner | schema + constraints + reconciliation | migration, reconciliation, sample/full-population tests | inaccurate/incomplete records | PARTIAL | MISSING | MISSING |
| GC-SEC-001 | Restrict privileged actions | DEE/security | authorization, separation, least privilege | IAM matrix, access review, logs | unauthorized access | PARTIAL | MISSING | MISSING |
| GC-SEC-002 | Protect software/supply chain | SDLC/security | CI, dependency/security controls | CI results, dependency scan, change approvals | malicious/vulnerable change | PARTIAL | MISSING | MISSING |
| GC-RES-001 | Recover authoritative state after database failure or response loss | PostgreSQL Release Authority | atomic rollback + replay + recovery | crash/replay tests, DB execution evidence | partial release/data inconsistency | PASS | MISSING | MISSING |
| GC-RES-002 | Recover expired outbox processing safely | PostgreSQL Recovery Outbox | lease expiry + `FOR UPDATE SKIP LOCKED` + retry | source, recovery test, execution evidence | stuck event / duplicate worker processing | PASS | MISSING | MISSING |
| GC-RES-003 | Recover abandoned idempotency operations without false completion | PostgreSQL Release Authority | `PROCESSING` lease/recovery policy | recovery implementation and test | permanently stuck or falsely completed release | MISSING | MISSING | MISSING |
| GC-AUD-001 | Preserve reproducible audit trail | CORE + evidence controls | witness/event/outbox + immutable references | event records, logs, commit SHA | missing/incomplete audit trail | PASS | MISSING | MISSING |
| GC-CHG-001 | Ensure audited code equals tested code | SDLC | immutable SHA + CI | commit, CI run, approval | unauthorized code drift | PASS | MISSING | MISSING |
| GC-IND-001 | Obtain independent re-performance of critical controls | Independent Assurance | clean-environment auditor/reviewer execution | independent test report and retained raw results | self-attestation risk | MISSING | MISSING | MISSING |

`*` = design status is preliminary until exact frozen implementation, gate artifacts, and reproducible test evidence are bound to the control.

## Required status rule

Do not convert `MISSING` to `PASS` by narrative. It requires a concrete evidence artifact and reproducible test.

`Operating = MISSING` means repository design/test evidence exists but operating-period evidence has not yet been established.

`Independent test = MISSING` means no independent re-performance has yet been retained as audit evidence.
