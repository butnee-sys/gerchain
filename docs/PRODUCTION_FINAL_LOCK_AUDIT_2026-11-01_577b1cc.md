# Exact-SHA Production Evidence Audit — 2026-11-01

**Snapshot SHA:** `577b1cc6ada49bd633729a08f4ce93473f7b0648`  
**PR:** [#111](https://github.com/butnee-sys/gerchain/pull/111), open and draft  
**Decision:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.

This is an evidence inventory, not a production certification. Evidence below is scoped to the stated SHA and run metadata. A PR merge checkout is not treated as an exact-head checkout unless the retained manifest proves the tested HEAD.

## 1. Same-SHA evidence inventory

| Gate | Run / artifact | Verified result | Limit |
|---|---|---|---|
| Production Gate | [41293346947](https://github.com/butnee-sys/gerchain/actions/runs/41293346947), artifact [13078771668](https://github.com/butnee-sys/gerchain/actions/runs/41293346947) | `PASS_CANDIDATE`; manifest binds canonical, commit, checked-out and PR-head SHA to `577b1cc6...`; 681 source files hashed; `source_hashes_complete=true`; no missing sources; 0 JUnit failures/errors | 18 environment-gated skips remain NOT RUN in this diagnostic |
| SHUUD/SANDBOX Product MVP | [41293346909](https://github.com/butnee-sys/gerchain/actions/runs/41293346909), artifact [13078056453](https://github.com/butnee-sys/gerchain/actions/runs/41293346909) | 108 passed, 0 failures, 0 errors, 0 skips; exit code 0 | Product MVP evidence only; not EAI production acceptance |
| DEE Security Gate | [41293346827](https://github.com/butnee-sys/gerchain/actions/runs/41293346827), job [124808996595](https://github.com/butnee-sys/gerchain/actions/runs/41293346827/job/124808996595) | Job success; PostgreSQL 16 service; `tests/test_dee_persistent_registry.py` reported 3 passed; other DEE test steps passed | **SHA binding failure:** log checks out PR merge SHA `ec2c4ff93750abe0959a3354374deebccb6790b5`, not head `577b1cc6...`; do not count as exact-head DEE evidence. No JUnit/artifact retained by this workflow |
| FINAL EAI/CORE Exact-SHA Gate | [41293346772](https://github.com/butnee-sys/gerchain/actions/runs/41293346772) | Run completed successfully; head SHA matches | Use its retained artifacts/logs for individual test claims; not a substitute for core-gates |
| Production PostgreSQL Gate | [41293346781](https://github.com/butnee-sys/gerchain/actions/runs/41293346781) | Run completed successfully; head SHA matches | Exact lifecycle report and migration evidence must be checked from its artifact before promoting to PASS_CANDIDATE |
| EAI PostgreSQL Re-performance | [41293346908](https://github.com/butnee-sys/gerchain/actions/runs/41293346908) | Run completed successfully; head SHA matches | Scope and test counts must be taken from its artifact/log |
| PostgreSQL Production Re-performance | [41293346812](https://github.com/butnee-sys/gerchain/actions/runs/41293346812) | Run completed successfully; head SHA matches | Verify embedded tested SHA and populated-vs-empty reconciliation scope before relying on it |
| Independent Production Audit | [41293346807](https://github.com/butnee-sys/gerchain/actions/runs/41293346807) | Automated audit job succeeded | Automated audit is not an independent human attestation or production certification |
| core-gates | [41293347123](https://github.com/butnee-sys/gerchain/actions/runs/41293347123) | Run event records exact head SHA; status `pending` | GitHub returns no jobs and no artifacts. It is not a test pass or fail. Root cause is not exposed by the available response |

### core-gates pending diagnosis

The workflow definition includes `pull_request` for PRs targeting `main`, `workflow_dispatch`, and a job `core-gates` on `ubuntu-latest` with PostgreSQL 16. The run was created from the PR event at `577b1cc6...`, but the Actions run endpoint reports `status=pending`, while the jobs endpoint returns an empty list and the artifacts endpoint returns an empty list. Thus the workflow was recognized, but no job execution record exists. The prior run `41288774875` at `e543ba...` was cancelled. The evidence does not identify whether the current pending state is due to runner scheduling, workflow orchestration, or another GitHub-side condition. Do not label it as a code test failure or a pass. A completed job with logs and JUnit at the frozen SHA is still required.

## 2. Twenty-one historical failures — current row disposition

The detailed #1–#21 table, original failure causes and same-candidate test-level dispositions are recorded in [MASTER_GATE_21_FAILURE_DISPOSITION_REGISTER.md](MASTER_GATE_21_FAILURE_DISPOSITION_REGISTER.md).

- #1: old `test_shuud_workflows_are_path_isolated` assertion was explicitly replaced by `test_shuud_workflows_are_separate_manual_entrypoints`; Production Gate artifact 13078771668 records 5/5 contract tests passed. The old assertion did not run unchanged.
- #2–#21: all 20 exact historical node IDs are present in Product MVP artifact 13078056453 and individually PASS; total product suite 108/108.
- The original 21-failure diagnostic at `0b097bc...` remains a historical fact. The newer results do not retroactively alter that run.
- This closes the 21 rows at **test level only**. SHUUD/SANDBOX remain distinct product scope and their deployment/release controls are not thereby accepted.

## 3. MG-07 through MG-14 — itemized evidence assessment

| Gate | What is present | What is not evidenced / required to close | Status |
|---|---|---|---|
| MG-07 Legacy authority-store freeze | Architecture and ledger authority documentation; record of legacy endpoint shutdown | Physical read-only/retirement proof for every legacy authority store; production route write-denial; negative write attempts; independent verification that no legacy path can mutate value | **OPEN** |
| MG-08 IAM/MFA and privileged access | Application-side security and authorization tests | Identity-provider export; enforced MFA policy and exception list; privileged-user inventory/review; least-privilege evidence; access revocation test; independent attestation | **OPEN** |
| MG-09 Observability and recovery | Runtime boot and automated restart/recovery tests | Production telemetry coverage; alert delivery exercise; incident runbook and response evidence; recovery/restart drill proving no duplicate value movement; retained logs and operator sign-off | **OPEN** |
| MG-10 Production-like performance | PostgreSQL concurrency and replay tests | Approved workload model; throughput/latency/error thresholds; capacity envelope; raw production-like load report; bottleneck disposition and signed acceptance | **PARTIAL / OPEN** |
| MG-11 Backup/restore/DR | No complete restore drill identified in this evidence set | Backup integrity; isolated restore; post-restore ledger/migration reconciliation; measured RPO/RTO; failover/DR exercise and sign-off | **OPEN** |
| MG-12 CI/release governance | Multiple successful exact-head workflow runs; workflow definitions | GitHub API reports `protected=false` for both `main` and `fix/withdraw-unverified-production-certificate`; no required status checks or branch protection enabled. Enable and independently verify rulesets/branch protection, required workflows/reviews, release permissions and immutable artifact provenance | **OPEN — protection currently disabled** |
| MG-13 Independent re-performance | Automated Independent Production Audit completed successfully | Named independent reviewer; independence/conflict statement; independently controlled environment and inputs; signed re-performance report bound to frozen SHA and deployment identity | **PARTIAL / OPEN** |
| MG-14 Evidence index and authorized approval | Run and artifact links are recorded in this audit and the 21-row register | Complete signed index mapping every control to artifact, SHA, environment, owner and expiry; explicit decision by the authorized approver; deployment identity and approval timestamp | **OPEN** |

No GitHub CI result can substitute for physical legacy-store freeze, identity-provider configuration, operational drills, disaster recovery, or an authorized approval. These require controlled operational evidence from the responsible system owners.

## 4. DEE PostgreSQL SHA correction required

The DEE workflow has a PostgreSQL 16 service and sets `DEE_POSTGRES_URL`. The test `test_postgresql_concurrent_rotation_only_one_wins` is part of `tests/test_dee_persistent_registry.py`. At run 41293346827, the job log confirms that file ran and reported 3 passed, but the checkout line is:

`HEAD is now at ec2c4ff93750abe0959a3354374deebccb6790b5`

The run metadata head is `577b1cc6ada49bd633729a08f4ce93473f7b0648`. Because the checkout and head differ, this log is not admissible as exact-577b1cc6 DEE PostgreSQL proof. Required correction: pin checkout to `${{ github.event.pull_request.head.sha || github.sha }}`, assert `git rev-parse HEAD` equals that value, generate a SHA-bound manifest, write JUnit output, and upload logs/JUnit as an artifact. Re-run on a frozen candidate SHA.

## 5. SHA and status rules

- A run's `head_sha` is not enough if the job checked out a different PR merge SHA.
- Keep artifacts with mismatched embedded SHA quarantined; do not rename or rewrite their provenance.
- `PASS_CANDIDATE` is an evidence status, not `PRODUCTION READY`.
- A later documentation commit changes the branch head. Evidence above remains a snapshot for `577b1cc6...`; any final candidate must rerun mandatory gates against its own exact SHA.
- Keep PR #111 open and draft until MG-07–MG-14, core-gates, independent sign-off and authorized approval are complete.

**MASTER GATE = OPEN; PRODUCTION READY = NOT VERIFIED; FINAL LOCK = OPEN.**
