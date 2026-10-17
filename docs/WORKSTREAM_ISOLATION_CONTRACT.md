# Workstream Isolation Contract

Status: ACTIVE
Applies to: fundamental GerChain architecture / EAI and SHUUD
Branch: `feat/ea21-transaction-aware-ledger`

## 1. Non-negotiable scope boundary

SHUUD is a separate product workstream. It is not part of the fundamental-architecture production-readiness claim and must not be used as a proxy for the readiness of CORE, EAI, Canonical Ledger, Canonical Escrow, Witness, Outbox, migration, or recovery controls.

The fundamental-architecture workstream must not depend on SHUUD runtime state, SHUUD application routes, SHUUD persistence, or SHUUD sandbox lifecycle.

## 2. CI separation

- `.github/workflows/core-gates.yml` owns the fundamental-architecture and EAI PostgreSQL production gate.
- `.github/workflows/shuud-sandbox-smoke.yml` owns only the SHUUD sandbox lifecycle and restart-recovery smoke.
- The SHUUD workflow must not contain or invoke the EA-35 PostgreSQL gate.
- The SHUUD workflow must trigger automatically only for SHUUD-owned paths: `shuud/**`, `tests/test_shuud_*.py`, and `sandbox/**`. It remains manually dispatchable for deliberate cross-workstream compatibility checks.
- Core production evidence is judged from the dedicated core gate, not from SHUUD workflow results.
- SHUUD failures must not be reported as fundamental-architecture failures; core failures must not be hidden by SHUUD success.

## 3. Change discipline

1. Do not modify SHUUD application code while executing fundamental-architecture closure work.
2. Do not add SHUUD tests to the fundamental-architecture gate.
3. Do not add fundamental-architecture production gates to the SHUUD workflow.
4. A change to a shared contract that could affect both workstreams requires an explicitly named cross-workstream compatibility run; it does not merge the two readiness claims.
5. Do not declare the fundamental architecture locked until its own exact-SHA PostgreSQL, recovery, reconciliation, security/governance, and independent re-performance evidence is complete.

## 4. Acceptance check

This contract is satisfied only when:
- SHUUD workflow has no EA-35/core production gate job;
- SHUUD workflow path filters exclude generic core paths;
- core-gates contains no SHUUD-specific tests;
- the two workstreams retain separate evidence and separate readiness dispositions.

A workflow edit is implementation evidence, not proof that a newly triggered workflow has passed.
