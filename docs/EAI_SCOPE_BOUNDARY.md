# EAI Scope Boundary and Application Isolation

Status: ARCHITECTURAL SCOPE INVARIANT — REQUIRED
Applies to: EAI / foundational production-readiness work
Branch at introduction: feat/ea21-transaction-aware-ledger

## 1. Non-negotiable separation

**SHUUD is a separate, independently scoped application. SHUUD is not part of EAI.**

**The SHUUD sandbox belongs to SHUUD only. It is not the EAI sandbox, EAI test environment, EAI deployment environment, or evidence of EAI production readiness.**

EAI means **Escrow as Infrastructure**. EAI production readiness is assessed against the canonical economic-infrastructure architecture, its authoritative PostgreSQL persistence, value-movement invariants, evidence graph, recovery, security, observability, and independently repeatable production verification.

SHUUD and its sandbox must not be included as EAI dependencies, EAI components, EAI test fixtures, EAI release gates, or EAI evidence sources unless a separately approved, explicit integration contract is introduced. No such integration is implied by shared ownership, repository proximity, naming, or earlier conversations.

## 2. Required classification rules

| Item | Correct scope | Must not be classified as |
|---|---|---|
| EAI | Foundational escrow-as-infrastructure architecture and production-readiness target | SHUUD app or sandbox |
| SHUUD | Separate independent application | EAI component or EAI sub-layer |
| SHUUD sandbox | SHUUD-owned isolated sandbox | EAI sandbox, PostgreSQL production proof, or EAI release evidence |
| EAI PostgreSQL verification | EAI-specific production persistence and runtime verification | SHUUD sandbox test |
| EAI CI / release evidence | Exact-SHA checks for EAI code and EAI-owned tests | SHUUD CI or sandbox results |

## 3. Evidence separation

Evidence is valid only for the scope, commit, environment, and test it actually verifies.

- A SHUUD test cannot prove EAI readiness.
- A SHUUD sandbox boot cannot prove EAI production boot.
- SHUUD application status must not change EAI status.
- EAI production status must not change SHUUD status.
- Shared repository presence does not establish runtime or architectural coupling.
- If a report mentions SHUUD while evaluating EAI, classify it as scope contamination and correct the report before using it as release evidence.

## 4. EAI production gate remains independent

EAI cannot be marked production-ready or locked until EAI-specific evidence verifies, at minimum:

1. canonical PostgreSQL schema and migration completeness;
2. production entrypoint and runtime authority;
3. durable escrow lifecycle and canonical Ledger operations;
4. atomic value movement with Witness, Outbox, and durable idempotency;
5. deep cross-store value-truth reconciliation;
6. fail-closed behavior and recovery without duplicate value movement;
7. security, observability, CI, and deployment/restart behavior;
8. exact-commit evidence and independent re-performance.

No SHUUD artifact substitutes for any item above.

## 5. Change control

Any future connection between SHUUD and EAI requires a separate, explicit architecture-change proposal defining the interface, ownership, trust boundary, failure isolation, data authority, and independent evidence requirements. Until that proposal is approved, the systems remain separate.

## 6. Repeated-finding response

Repeated appearance of SHUUD or its sandbox in EAI readiness work is not a reason to merge scopes. It is a classification defect to be corrected at the source: plan, test selection, environment variables, CI workflow, deployment configuration, and evidence report must each label their owning system explicitly.

**Invariant: EAI is verified on EAI-owned runtime and evidence. SHUUD is verified on SHUUD-owned runtime and sandbox. Neither is proof of the other.**
