# EA-35 — Production PostgreSQL Evidence and Lock Status

**Branch:** `feat/ea21-transaction-aware-ledger`  
**Verified implementation SHA:** `52e2e1bce5952bbe7a91ac091dcf3c5eb5ba11e4`  
**Evidence date:** 2026-10-07

## Status

**EA-35 PostgreSQL/EAI evidence boundary: VERIFIED / PARTIALLY LOCKED**

The executable production implementation is evidence-locked at SHA `52e2e1bce5952bbe7a91ac091dcf3c5eb5ba11e4`. Subsequent commits in this evidence record are documentation-only and do not alter executable production code.

Fresh GitHub Actions evidence confirms real PostgreSQL execution on the current implementation line.

## Fresh exact-SHA workflow evidence — 2026-10-07

Current implementation SHA `52e2e1bce5952bbe7a91ac091dcf3c5eb5ba11e4`:

| Evidence | Workflow run | Result |
|---|---:|---|
| EA-35 PostgreSQL production smoke | 37556985851 | SUCCESS |
| Production PostgreSQL re-performance | 37556985723 | SUCCESS |
| Production PostgreSQL E2E | 37556985756 | SUCCESS |
| Independent PostgreSQL evidence | 37556985808 | SUCCESS |
| production-postgres | 37556985832 | SUCCESS |
| PostgreSQL production smoke | 37556985860 | SUCCESS |

### EA-35 PostgreSQL production smoke

Run `37556985851` / job `112585373556`.

The workflow started a real PostgreSQL 16 service and executed:

`python -m pytest -q tests/integration/test_production_entrypoint_bootstrap.py tests/integration/test_postgresql_production_smoke.py`

Result:

**2 passed in 0.40s**

Verified:
- production entrypoint bootstrap;
- canonical ledger authority;
- durable PostgreSQL escrow lifecycle;
- FUND → LOCK → RELEASE;
- RELEASE replay idempotency;
- REFUND authoritative destination protection;
- CANCEL state-only path;
- SETTLEMENT through Canonical Ledger;
- deep value-truth reconciliation.

### Production PostgreSQL re-performance

Run `37556985723` / job `112585373378`.

Executed against PostgreSQL 16:

`pytest -q -m integration tests/test_production_postgresql_runtime.py`

Result:

**1 passed in 0.69s**

Verified:
- PostgreSQL production runtime construction;
- canonical authority;
- required canonical tables;
- migration/bootstrap path.

### Production PostgreSQL E2E

Run `37556985756` / job `112585373235`.

Executed:

`pytest -q tests/integration/test_production_postgresql_e2e.py`

Result:

**1 passed in 0.50s**

Verified:
- real PostgreSQL boot;
- FUND;
- LOCK;
- RELEASE;
- persisted balances;
- durable escrow state;
- deep value-truth reconciliation.

### Independent PostgreSQL evidence

Run `37556985808` / job `112585373255`.

Executed:

`pytest -q tests/independent/test_postgresql_independent_evidence.py`

Result:

**1 passed in 0.40s**

This verification reads raw persisted PostgreSQL facts independently of the runtime result:
- canonical balances;
- movement records;
- movement operation and escrow binding;
- integrity hashes;
- escrow state/version;
- witness records;
- outbox records;
- idempotency records.

## Migration authority correction

The current `ProductionRuntimeFactory` no longer treats ORM `create_all()` as the production schema authority.

Production initialization now:

**PostgreSQL canonical migration runner → schema verification → canonical runtime**

The migration runner serializes publication with PostgreSQL advisory locking and records schema history/checksums.

ORM metadata remains only an additive compatibility guard after migration.

## Important boundary

These results prove **fresh PostgreSQL execution on the current implementation line**.

They do **not** by themselves constitute:
- organizational IAM/MFA assurance;
- privileged-access review;
- main-branch governance evidence;
- external independent assurance;
- final global production lock.

Some broader workflows were cancelled because newer branch executions superseded them. A cancelled workflow is not treated as a failure and is not used as positive evidence.

## EAI conclusion

The fresh evidence supports the production path:

**Escrow-as-Infrastructure → durable PostgreSQL escrow → Canonical Ledger → Witness → Outbox → Idempotency → Deep Value Truth Reconciliation**

EAI remains an infrastructure principle implemented through the frozen architecture; it is not introduced as a new architecture layer.

## Lock boundary

**PostgreSQL production evidence: LOCKED at implementation SHA `52e2e1bce5952bbe7a91ac091dcf3c5eb5ba11e4`.**

**EA-35 final architecture lock: NOT YET LOCKED.**

Remaining final-lock gates are governance/assurance closure and final immutable evidence-index reconciliation. No executable architecture change is authorized under this evidence lock without an explicit architecture-change proposal.

No product-layer work is authorized by this document.
