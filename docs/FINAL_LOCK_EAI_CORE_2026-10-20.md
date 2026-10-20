# FINAL LOCK — GERCHAIN EAI / CORE / PostgreSQL
**Decision date:** 2026-10-20  
**Decision:** FINAL LOCK  
**Scope:** GerChain fundamental architecture, EAI, Canonical Ledger, PostgreSQL transaction boundary, and previously closed CORE gates.  
**Out of scope:** SHUUD and SANDBOX applications; they are separate applications and are not part of GerChain EAI or this lock.

## 1. Final scope decision
This record closes the scope and gate-management loop. Previously verified and accepted PostgreSQL and CORE gates are inherited as CLOSED from the prior work evidence. They must not be reopened merely because a later summary, unrelated workflow, SHUUD run, or SANDBOX run reports a separate status.

## 2. No-repeat rule
- Do not rerun or duplicate PostgreSQL/CORE checks already accepted as closed.
- Do not reopen closed gates based only on stale documentation, a different commit's unrelated workflow, or app-specific SHUUD/SANDBOX results.
- Do not create new findings by reclassifying previously resolved defects without new, specific contradictory evidence.
- Do not run SHUUD or SANDBOX gates as a prerequisite for EAI/CORE FINAL LOCK.
- Any future exception requires a concrete new regression or integrity incident, the exact affected gate, and evidence tied to the relevant commit. Otherwise, status remains inherited and closed.

## 3. Authority and architecture invariants
- Canonical architecture remains frozen; this record does not redesign or extend it.
- EAI means Escrow as Infrastructure; it is not a new architecture layer and does not create a second Escrow Engine.
- Canonical Ledger remains the single authoritative value-movement boundary.
- One authoritative Witness path and one production Outbox path; no parallel truth authority.
- Value release remains Decision → Authorization → Release.
- Legacy or application-owned stores do not become production value authorities.
- SHUUD and SANDBOX remain separate applications and cannot mutate or redefine EAI/CORE gate status.

## 4. Final gate disposition
| Gate | Final disposition | Rule |
|---|---|---|
| Canonical architecture | LOCKED | No silent architecture changes |
| Previously verified PostgreSQL gates | CLOSED / INHERITED | No duplicate rerun |
| Previously verified CORE gates | CLOSED / INHERITED | No duplicate rerun |
| EAI scope and authority boundary | LOCKED | No second escrow/value authority |
| SHUUD | EXCLUDED | Separate application |
| SANDBOX | EXCLUDED | Separate application |
| Duplicate/repeated checks | STOPPED | Reopen only on concrete new regression evidence |

## 5. Change control
This is a scope and gate-management lock, not a claim of a new test run or external certification. Existing evidence remains the evidence of record. No new GREEN claim is created by this document. Changes after this lock require a narrowly scoped change request identifying the invariant affected, the new evidence, and the reason a previously closed gate must be reopened.

**Final instruction: preserve the closed gates, stop duplicated checks, and proceed only with explicitly authorized FINAL LOCK work.**
