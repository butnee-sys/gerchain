# EA-35 Exact-SHA Evidence Register

**Evidence target branch:** `feat/ea21-transaction-aware-ledger`  
**Exact tested commit SHA:** `52419f4750ec062c9c5ecf458e4a4f0e6bdd8099`  
**Evidence captured:** 2026-10-18 (UTC)  
**Decision:** PostgreSQL gates PASS for this SHA; overall production lock NOT AUTHORIZED.

This is a detached evidence register on branch `evidence/ea35-52419f4750ec062c`. It does not change the tested source branch or imply that this register's own commit was tested.

## 1. Exact-SHA workflow results

| Gate | Workflow run ID | Conclusion | Exact head SHA | Artifact |
|---|---:|---|---|---|
| PostgreSQL production migration gate | 39103010592 | SUCCESS | `52419f4750ec062c9c5ecf458e4a4f0e6bdd8099` | `postgres-migration-gate-52419f4750ec062c9c5ecf458e4a4f0e6bdd8099` |
| PostgreSQL concurrency and migration gate | 39103010598 | SUCCESS | `52419f4750ec062c9c5ecf458e4a4f0e6bdd8099` | No artifact published |
| Production Readiness Gates | 39103010597 | SUCCESS | `52419f4750ec062c9c5ecf458e4a4f0e6bdd8099` | No artifact published |
| EAI PostgreSQL Re-performance | 39103010637 | SUCCESS | `52419f4750ec062c9c5ecf458e4a4f0e6bdd8099` | `eai-postgres-reperformance-52419f4750ec062c9c5ecf458e4a4f0e6bdd8099` |
| core-gates full repository suite | 39103010569 | IN PROGRESS at evidence capture | `52419f4750ec062c9c5ecf458e4a4f0e6bdd8099` | Pending |

Run links:
- https://github.com/butnee-sys/gerchain/actions/runs/39103010592
- https://github.com/butnee-sys/gerchain/actions/runs/39103010598
- https://github.com/butnee-sys/gerchain/actions/runs/39103010597
- https://github.com/butnee-sys/gerchain/actions/runs/39103010637
- https://github.com/butnee-sys/gerchain/actions/runs/39103010569

## 2. Artifact integrity and lifecycle test counts

### PostgreSQL migration gate

- Artifact ID: `12127457127`
- Artifact SHA-256 digest (GitHub Actions metadata): `sha256:14e272e8a4c7becd5d89ec7455b7ff137ec7711d909097b05c9479a7831272c2`
- Artifact URL: https://github.com/butnee-sys/gerchain/actions/runs/39103010592
- Report path: `production-postgres/migration-lifecycle-report.json`
- `commit_sha` = `52419f4750ec062c9c5ecf458e4a4f0e6bdd8099`
- `workflow_sha` = `52419f4750ec062c9c5ecf458e4a4f0e6bdd8099`
- `sha_match` = `true`
- JUnit: **20 tests, 0 failures, 0 errors, 0 skipped**, 1 suite.
- Migration history: **16 applied canonical migration versions**, contiguous from 1 through 16; recorded checksums match the migration runner's expected registry.
- Source SHA-256 inventory: six required source/workflow files recorded.
- Migration SHA-256 inventory: 26 SQL files recorded.

### EAI PostgreSQL re-performance

- Artifact ID: `12126908895`
- Artifact SHA-256 digest (GitHub Actions metadata): `sha256:cc3127fddca9b4172bf2ac97a729b5f6fc495ed9d7dfac3fe715789aa7f9ffab`
- Artifact name: `eai-postgres-reperformance-52419f4750ec062c9c5ecf458e4a4f0e6bdd8099`
- Artifact URL: https://github.com/butnee-sys/gerchain/actions/runs/39103010637

GitHub's artifact digest binds the uploaded ZIP to its run metadata; the digest cannot be embedded inside the same ZIP without creating a self-reference.

## 3. Security and repository governance

- Main branch API reports `protected: false`.
- Required status checks are not enforced (`enforcement_level: off`, empty required checks).
- Repository rulesets API returned an empty list.
- Branch-protection detail endpoint returned HTTP 403 to the connected integration; therefore, settings beyond the readable branch summary cannot be independently inspected here.
- IAM identity/role inventory, privileged-account MFA enforcement, dated privileged-access review, and production least-privilege review remain **OPEN — external administrative evidence required**.

## 4. Decision

The exact-SHA PostgreSQL migration gate, PostgreSQL concurrency/migration gate, Production Readiness Gates, and EAI PostgreSQL re-performance are recorded as SUCCESS for `52419f4750ec062c9c5ecf458e4a4f0e6bdd8099`. The lifecycle report confirms nonzero tests and exact SHA binding.

However:
1. The full `core-gates` suite was still in progress when this register was captured.
2. Main branch protection and required status-check enforcement are absent in the readable repository metadata.
3. IAM/MFA and privileged-access review evidence is not supplied.
4. Independent production approval and all remaining production-lock gates must be closed separately.

**EA-35 status: IN PROGRESS / NOT LOCKED. Production lock is NOT AUTHORIZED.**
