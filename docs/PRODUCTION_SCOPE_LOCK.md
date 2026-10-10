# PRODUCTION SCOPE LOCK — FUNDAMENTAL ARCHITECTURE / EAI

Status: FINAL-LOCK DIRECTION
Effective scope: Fundamental Architecture + EAI (Escrow as Infrastructure)

## Excluded from this production gate

The following are downstream application work and MUST NOT participate in the fundamental architecture/EAI acceptance result:

- SHUUD Command Layer
- SHUUD Sandbox Smoke
- SHUUD sandbox/application tests
- product/application-specific smoke tests

SHUUD is an application that runs on the completed fundamental infrastructure. It is not part of EAI and does not determine EAI production readiness.

## PostgreSQL Concurrency / core-gates

PostgreSQL Concurrency is a fundamental infrastructure concern. Its acceptance result is determined only by its dedicated canonical concurrency test and current exact-SHA evidence. Historical failures caused by workflow coupling, stale tests, or downstream SHUUD execution MUST NOT be reclassified as current fundamental-architecture failures.

The core-gates workflow MUST execute only the canonical fundamental architecture/EAI acceptance set. Downstream application workflows are independent and MUST NOT block this gate.

## Final lock invariant

Fundamental Architecture/EAI readiness = only fundamental architecture, canonical value-flow, escrow-as-infrastructure, transaction correctness, recovery, auditability, security, observability, performance, deployment and independent evidence.

SHUUD readiness is a separate later acceptance track.

No downstream application failure may mutate, reopen, or invalidate the Fundamental Architecture/EAI lock unless a direct dependency violation is demonstrated by a dedicated fundamental-architecture test.

## Current direction

Do not add SHUUD tests to core-gates.
Do not add SHUUD sandbox smoke to EAI gates.
Do not report SHUUD failures as EAI/core failures.
Do not use SHUUD to define production readiness of the fundamental architecture.
