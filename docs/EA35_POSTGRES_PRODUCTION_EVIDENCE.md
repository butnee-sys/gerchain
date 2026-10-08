# EA-35 PostgreSQL Production Evidence

## Evidence status

**Status: VERIFIED — NOT YET PRODUCTION LOCKED**

Latest verified branch tip:
`bef54b697c2d35673fcfb5becd7061f1de8f308f`

Original evidence publication commit:
`f63218b7833589a11a94e2e085550a475c8dfa25`

Repository:
`butnee-sys/gerchain`

Branch:
`feat/ea21-transaction-aware-ledger`

## Exact GitHub Actions evidence

### 1. PostgreSQL production gate

Run: `37707140772`

Job: `postgresql-production-gate`

Conclusion: **success**

Verified steps:
- Python syntax gate
- production factory and canonical persistence
- production entrypoint boot against PostgreSQL
- concurrent PostgreSQL migration bootstrap
- deep reconciliation tests
- EAI production re-performance
- real PostgreSQL production value-flow gate

### 2. PostgreSQL production value suite

Run: `37707140825`

Job: `postgres-production`

Conclusion: **success**

Verified steps:
- production PostgreSQL migration and boot
- production PostgreSQL value flow
- deep value truth suite

### 3. Independent PostgreSQL evidence

Run: `37707140836`

Job: `independent-postgresql-evidence`

Conclusion: **success**

Verified:
- independent persisted-value verification

### 4. EAI production proof

Run: `37707140769`

Job: `eai-production-proof`

Conclusion: **success**

Verified:
- EAI PostgreSQL production proof

### 5. Exact-SHA production re-performance

Run: `37707140771`

Job: `production-postgresql-reperformance`

Conclusion: **success**

Verified:
- fresh PostgreSQL production re-performance against the current branch tip

## What is now proven

The exact evidence commit has demonstrated, against a real PostgreSQL service in GitHub Actions:

1. PostgreSQL is required by the production factory.
2. Canonical production migrations bootstrap successfully.
3. Migration bootstrap is safe under concurrent initialization.
4. Production entrypoint boots against PostgreSQL.
5. Canonical Ledger authority is established.
6. Legacy PostgreSQL Release authority is not selected by the production factory.
7. Canonical persistence tables are present.
8. Canonical production value-flow tests pass.
9. Deep value-truth reconciliation tests pass.
10. Independent persisted-value verification passes.
11. EAI production proof passes.

## Important boundary

This evidence proves the tested production PostgreSQL construction and value-flow/reconciliation gates.

It does **not** by itself constitute final production lock, external audit attestation, deployment approval, IAM/MFA closure, disaster-recovery acceptance, or independent organizational sign-off.

Therefore:

**EA-35 = VERIFIED / IN PROGRESS / NOT LOCKED**

Latest verification: exact branch tip `bef54b697c2d35673fcfb5becd7061f1de8f308f` has successful production PostgreSQL, production re-performance, EAI, independent evidence, core-gates, CodeQL, CORE reconciliation, and SHUUD checks.

Next lock gates remain:
- security/IAM/MFA governance evidence
- operational deployment readiness
- recovery/DR evidence
- independent re-performance and acceptance
- final production lock decision
