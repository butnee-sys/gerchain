# MASTER WORK PLAN — STEP 1 FINAL LOCK

Date: 2026-10-19
Repository: `butnee-sys/gerchain`
Branch: `feat/ea21-transaction-aware-ledger`
Scope: Step 1 — INVENTORY / MAP only.
Decision: **STEP 1 INVENTORY/MAP — LOCKED (scope-limited)**.
This does not declare the overall architecture, EAI, or production runtime production-ready.

## 1. Locked canonical architecture references

- Frozen architecture: `docs/DEE_ARCHITECTURE_FREEZE.md`
- Production runtime value authority audit: `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md`
- Runtime value-authority dependency map: `docs/EA34_RUNTIME_VALUE_AUTHORITY_MAP.md`
- Legacy value authority freeze: `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md`
- Deep value-truth reconciliation: `persistence/deep_value_reconciliation.py`
- Production factory: `services/gerchain_runtime_factory.py`
- Production entrypoint: `production_entrypoint.py`

## 2. Inventory/map closure checklist

| Inventory area | Recorded canonical position | Step 1 result |
|---|---|---|
| Frozen architecture path and adapters | DE → DEE → G3 → NEF + GerChain → EXIM → I2B → MultiConnector; explicit adapters | COMPLETE |
| Value-truth authority | `gerchain_ledger_accounts` + `gerchain_ledger_movements` | COMPLETE |
| Mutation boundary | `PostgreSQLAtomicLedger.transfer_in_transaction` | COMPLETE |
| Durable escrow truth | Canonical Escrow aggregate and explicit lifecycle operations | COMPLETE |
| Operation routing | FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT mapped to canonical persistence paths | COMPLETE |
| Evidence path | Witness + Outbox + durable idempotency + deep reconciliation | COMPLETE |
| Runtime construction | Production entrypoint → ProductionRuntimeConfig → ProductionRuntimeFactory → Canonical Ledger configuration | COMPLETE |
| Legacy bypass surfaces | API v1 and Web UI legacy mutations identified and fail-closed in the audit record | COMPLETE |
| Alternate/non-authoritative stores | MoneyLedger, ReleaseAccount, AccountBalance, SQLite/legacy paths inventoried as non-authoritative | COMPLETE |
| Remaining assurance gates | Migration-upgrade compatibility, restart/recovery same-SHA proof, all required CI, IAM/MFA, branch governance, physical legacy retirement, independent review | COMPLETE AS OPEN ITEMS; NOT CLAIMED PASSED |

## 3. Numeric completion measure

- Inventory/map categories recorded: **10 / 10 = 100%**.
- Canonical runtime/value authority route mapped: **100% of the required operation families listed in this scope**.
- Unresolved assurance items deliberately retained as open: **7**.
- Production-readiness / overall architecture lock: **NOT LOCKED**.

The 100% value measures completion of the inventory-and-map artifact, not proof that every mapped component passed production verification. The current commit's combined status evidence that has been directly retrieved in this work shows Snyk success only; it does **not** establish that all required CI workflows passed. No broader green claim is made.

## 4. Final lock boundary

The inventory/map is now frozen as the baseline for Step 2. Any newly discovered authority, write path, duplicate store, adapter bypass, or runtime fallback must be logged as a Step 2 discrepancy against this baseline; it must not be silently added to Step 1.

**FINAL LOCK: STEP 1 — INVENTORY / MAP: CLOSED.**
**FINAL LOCK: OVERALL FUNDAMENTAL ARCHITECTURE / EAI PRODUCTION: NOT LOCKED.**

## 5. Step 2 opened — ERROR / DUPLICATE / EXCESS

Step 2 starts from the following first-pass discrepancy register. These are audit targets, not all confirmed defects; each must be verified against current code/schema before remediation.

| ID | Audit target | Risk to test | Initial status |
|---|---|---|---|
| S2-01 | Legacy balance authorities: MoneyLedger, ReleaseAccount, AccountBalance | Competing value truth | OPEN — verify remaining references and reachable production paths |
| S2-02 | Legacy escrow authorities: ReleaseEscrow and SQLite escrow state | Competing escrow truth | OPEN — verify reads/writes and migration dependencies |
| S2-03 | Witness representations: TransactionWitness vs ReleaseWitness / in-memory WitnessChain | Duplicate or non-authoritative evidence | OPEN — distinguish canonical evidence from projections |
| S2-04 | Outbox representations: `outbox` vs `gerchain_outbox_events` | Duplicate delivery authority | OPEN — identify all producers/consumers and transaction semantics |
| S2-05 | Idempotency implementations: in-memory IdempotencyEngine vs durable records | Replay divergence | OPEN — classify test-only vs production references |
| S2-06 | Runtime mode conflation: `runtime_mode` and release-specific PostgreSQL flags vs canonical-ledger authority | Incorrect readiness/authority inference | OPEN — inspect every gate and fallback |
| S2-07 | Production factory schema creation vs versioned migrations | `create_all` masking incomplete upgrade paths | OPEN — inspect migration registry and supported prior-schema upgrade |
| S2-08 | Direct SQL/state mutation and alternate entrypoints | PDEIZ/canonical boundary bypass | OPEN — search routes, CLI, UI, workers, scripts |
| S2-09 | Escrow CREATE durability and lifecycle schema parity | Missing or partial canonical aggregate | OPEN — compare model, migrations, constraints, and runtime |
| S2-10 | Duplicate operation/event identifiers and movement/evidence linkage | Orphan, mismatched, or duplicate value evidence | OPEN — reconcile transaction_id, operation, escrow_id, witness, outbox, idempotency |

### Step 2 exit criteria

1. Every target above is confirmed or rejected with file/schema/test evidence.
2. Every confirmed issue has severity, root cause, affected authority boundary, and minimal correction.
3. No removal or migration is performed before dependency and data-retention checks.
4. All proposed changes preserve the frozen architecture and single-authority invariants.
5. Step 2 closes only after the discrepancy register is reconciled and regression evidence is recorded.

**Step 2 status: IN PROGRESS / NOT LOCKED.**
