# FINAL LOCK — Seven-Step Evidence Register

**Repository:** `butnee-sys/gerchain`  
**Working branch:** `feat/ea21-transaction-aware-ledger`  
**Overall status:** IN PROGRESS / NOT LOCKED  
**Rule:** A step is added to this register only with traceable repository evidence. Source inspection is not equivalent to a successful production boot, CI pass, or independent re-performance.

## Seven-step sequence

1. Runtime entrypoint/import dependency trace.
2. Replacement map for every active or legacy path.
3. Quarantine legacy paths from production execution.
4. Migrate tests to canonical runtime boundaries.
5. Delete legacy code only after dependency count is zero.
6. Full capability / second-owner audit.
7. Final CORE lock only at **0 DUPLICATE / 0 MISSING / 0 BYPASS**, with exact-SHA runtime and CI evidence.

## Step 1 — Runtime entrypoint/import dependency trace

**Step result:** SOURCE TRACE VERIFIED; RUNTIME EXECUTION NOT YET VERIFIED  
**Added to FINAL LOCK register:** YES  
**Production lock:** NOT GRANTED

### Evidence reviewed

| Evidence | Repository path | Observed fact |
|---|---|---|
| E1-01 | `Dockerfile` (blob `b1996544b24233b7a295e59d9a4286f9468caaff`) | Container command is `python production_entrypoint.py`; Docker does not launch `node_cli.py`. |
| E1-02 | `production_entrypoint.py` (blob `7d466b715af03d982efbd41306959dc758bb0542`) | Validates PostgreSQL URL and required environment; positive integer amount; creates PostgreSQL engine; constructs runtime via `ProductionRuntimeFactory`; checks canonical-ledger authority; runs `SELECT 1`; disposes engine on failure/shutdown. |
| E1-03 | `services/gerchain_runtime_factory.py` (blob `b130c64f17d114efaef28d80173c026c98bd84c7`) | Applies versioned migrations, checks canonical schema, then configures `GerchainRuntime` with `configure_canonical_ledger` and calls `require_canonical_ledger_authority`. |
| E1-04 | `services/gerchain_runtime.py` | Production mode is attached explicitly to the canonical Ledger session factory; the class also imports legacy in-memory components, so their presence in the import graph is not treated as proof of production authority. |
| E1-05 | `node_cli.py` (blob `0784c11305e4b1e7feba6818f507a92c4cfea2be`) | Legacy CLI instantiates `NEFStateEngine` and `TransactionManager`; it is not the Docker CMD target. |
| E1-06 | `docker-compose.yml` (blob `89fd8d9b72e48b034fdae3ccaa4f656fa06fe6db`) | Compose passes PostgreSQL URL and escrow/currency/witness configuration to the production container. |

### Trace conclusion

```text
Dockerfile
  → production_entrypoint.py
  → ProductionRuntimeConfig / ProductionRuntimeFactory
  → versioned PostgreSQL migrations + canonical schema assertions
  → GerchainRuntime.configure_canonical_ledger(...)
  → require_canonical_ledger_authority()
  → PostgreSQL SELECT 1
  → long-running worker
```

The Docker production entrypoint is separated from the legacy `node_cli.py` path. The runtime class still imports memory/test components, so Step 1 does **not** claim those legacy components have been physically removed or that every possible non-Docker entrypoint is quarantined. Those are Steps 2–5.

### Quantified evidence at Step 1

- Production Docker command traced: **1/1**
- Production entrypoint-to-factory call chain traced: **1/1**
- Canonical Ledger authority assertion in startup path: **1**
- Database reachability probe in startup path: **1** (`SELECT 1`)
- Explicit required environment-variable groups: **5** (database URL; escrow ID; amount; currency; witness ID)
- Legacy CLI identified as a separate non-Docker path: **1**
- Source-trace items in this register: **6**
- Actual production PostgreSQL boot with retained run ID: **0 evidenced here**
- Exact-SHA successful CI run verified in this step: **0 evidenced here**
- Independent re-performance artifacts: **0 evidenced here**

### Step 1 acceptance boundary

The static runtime/import trace is complete and recorded. The step is **not** an end-to-end production verification: a live PostgreSQL boot, migration-history validation against the target database, operation-level tests, and exact-commit CI evidence must be retained before the overall FINAL LOCK can be granted.

## Step 2 — Replacement map

**Status:** OPEN — next step.  
Acceptance requires every identified legacy/alternate runtime or mutation path to map to one canonical replacement or an explicit deny/quarantine rule, with source path and test evidence. No legacy deletion is allowed before Step 5 dependency count is zero.


## Step 2 — Replacement map

**Step result:** REPLACEMENT MAP RECORDED; BYPASS FINDING OPEN  
**Added to FINAL LOCK register:** YES  
**Production lock:** NOT GRANTED

### Source paths checked

| Evidence | Repository path | Observed fact |
|---|---|---|
| E2-01 | `Dockerfile` (blob `b1996544b24233b7a295e59d9a4286f9468caaff`) | Container CMD is `python production_entrypoint.py`. |
| E2-02 | `production_entrypoint.py` (blob `7d466b715af03d982efbd41306959dc758bb0542`) | Requires PostgreSQL URL and required configuration, constructs the factory, asserts canonical-ledger authority, and probes database reachability with `SELECT 1`. |
| E2-03 | `services/gerchain_runtime_factory.py` (blob `b130c64f17d114efaef28d80173c026c98bd84c7`) | Applies versioned migrations, asserts canonical schema, and configures Canonical Ledger authority. |
| E2-04 | `persistence/atomic_ledger.py` | Canonical value movement/account boundary. |
| E2-05 | `persistence/canonical_ledger_read.py` | Canonical balance read boundary. |
| E2-06 | `persistence/fund_escrow.py` | Canonical FUND. |
| E2-07 | `persistence/lock_escrow.py` | Durable, state-only LOCK. |
| E2-08 | `persistence/release_escrow.py` | Canonical RELEASE. |
| E2-09 | `persistence/refund_escrow.py` | Canonical REFUND using authoritative refund destination. |
| E2-10 | `persistence/cancel_escrow.py` | Canonical CANCEL and any required reversal. |
| E2-11 | `persistence/settlement_coordinator.py` | Settlement orchestration over Canonical Ledger. |
| E2-12 | `api/v1.py` (blob `09181c4651e15cd78030fad057db20ad865dab61`) | Legacy SQLite mutation guards raise HTTP 410. |
| E2-13 | `node_cli.py` (blob `0784c11305e4b1e7feba6818f507a92c4cfea2be`) | Legacy in-memory NEFStateEngine + TransactionManager path remains in repository; not Docker CMD. |
| E2-14 | `network/api_server.py` (blob `817e3aef598c73afceb8e480ccab106f909dd2b8`) | Alternate API server imports legacy in-memory NEF/TransactionManager runtime. |
| E2-15 | `gerchain/web_ui.py` (blob `7722791fd5a7d7ee961829c250259f1d9c7bbaea`) | `/api/v1/escrow/transfer` mutates application-owned account balances and `/api/v1/evidence/verify-and-release` directly mutates balances after evidence verification. Both remain active in the inspected source. |

### Replacement map

| Existing path/capability | Canonical replacement or rule | Status |
|---|---|---|
| Docker production boot | `production_entrypoint.py → ProductionRuntimeFactory → PostgreSQL Canonical Ledger` | MAPPED; source trace only |
| Account create / balance read | `PostgreSQLAtomicLedger` / `CanonicalLedgerRead` | MAPPED |
| FUND | `fund_escrow_in_transaction → AtomicValueTransaction` | MAPPED |
| LOCK | `lock_escrow_in_transaction` | MAPPED |
| RELEASE | `release_escrow_in_transaction → AtomicValueTransaction` | MAPPED |
| REFUND | `refund_escrow_in_transaction` | MAPPED |
| CANCEL | `cancel_escrow_in_transaction` | MAPPED |
| SETTLEMENT | `SettlementCoordinator → PostgreSQLAtomicLedger.transfer_in_transaction` | MAPPED |
| Legacy SQLite API mutation | Deny with HTTP 410; valid requests must use controlled runtime boundary | Guard present; tests/re-performance still required |
| `node_cli.py` / `network/api_server.py` | Canonical production runtime or explicit test-only quarantine | NOT QUARANTINED |
| Web UI `/api/v1/escrow/transfer` | Controlled runtime request → validation/authorization → Canonical Ledger transaction | **ACTIVE BYPASS — OPEN** |
| Web UI `/api/v1/evidence/verify-and-release` | Controlled RELEASE boundary; evidence alone must not mutate application-owned balances | **ACTIVE BYPASS — OPEN** |
| Legacy `MoneyLedger`, `ReleaseAccount`, `AccountBalance`, SQLite stores | Canonical Ledger only; old stores read-only/non-authoritative | Freeze document exists; physical quarantine/removal not proven |

### Quantified Step 2 result

- Canonical operation families mapped: **7** (account/read, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT).
- Runtime and persistence source paths reviewed for the map: **15**.
- Legacy SQLite mutation guards observed: **2**.
- Alternate in-memory runtime entrypoints identified: **2**.
- Active application-owned financial mutation routes identified: **2**.
- Known active bypasses still open: **2**.
- Legacy paths proven physically removed: **0**.
- Live PostgreSQL operation/reconciliation runs retained: **0 evidenced here**.

**Acceptance:** MAP COMPLETE / LOCK BLOCKED. Step 3 must quarantine the two active Web UI bypasses and classify/quarantine alternate in-memory entrypoints. Do not delete legacy code before Step 5 dependency count is zero.
