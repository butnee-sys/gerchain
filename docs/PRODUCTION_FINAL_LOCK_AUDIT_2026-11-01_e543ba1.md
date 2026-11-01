# Production Final Lock Evidence Audit — 2026-11-01

**Candidate SHA reviewed:** `e543ba112ff2c311b50ec7b7a8697b326e6d6b23`  
**Branch:** `fix/withdraw-unverified-production-certificate`  
**PR:** [#111](https://github.com/butnee-sys/gerchain/pull/111) — open, draft  
**Decision:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.

This is an evidence audit, not a certification or approval.

## 1. Exact-SHA run inventory

The following completed runs identify the candidate SHA above:

| Workflow | Run / artifact | Result and scope |
|---|---|---|
| Production Gate | [41288774980](https://github.com/butnee-sys/gerchain/actions/runs/41288774980), artifact 13076497382 | Success; segmented EAI diagnostic reports 0 failures, 18 skips; per-file JUnit retained |
| Production PostgreSQL Gate | [41288774828](https://github.com/butnee-sys/gerchain/actions/runs/41288774828), artifact 13076058399 | Success; `PASS_CANDIDATE`; exact SHA match; 13/13 source hashes complete; 17/17 migrations and applied checksums match; migration history exact; lifecycle JUnit 6/6, 0 failures/errors/skips |
| EAI PostgreSQL Re-performance | [41288774705](https://github.com/butnee-sys/gerchain/actions/runs/41288774705), artifact 13075339867 | Success; core-gates suite 56/56 and deep reconciliation 24/24 |
| PostgreSQL Production Re-performance | [41288774805](https://github.com/butnee-sys/gerchain/actions/runs/41288774805), artifact 13076387227 | Success; `PASS_CANDIDATE`; exact SHA match; 17 migrations applied; production boot PASS; 25 PostgreSQL tests passed |
| FINAL EAI/CORE Exact-SHA Gate | [41288774889](https://github.com/butnee-sys/gerchain/actions/runs/41288774889), artifact 13076162852 | Success; exact-SHA evidence retained |
| SHUUD/SANDBOX Product MVP | [41288774986](https://github.com/butnee-sys/gerchain/actions/runs/41288774986), artifact 13076670356 | Success; 108 passed, 0 failures, 0 errors, 0 skipped |
| Independent Production Audit | [41288774878](https://github.com/butnee-sys/gerchain/actions/runs/41288774878), artifact 13076083233 | Automated audit success; its verdict expressly says this is not production-ready certification |
| Production Readiness Gates | [41288774751](https://github.com/butnee-sys/gerchain/actions/runs/41288774751) | Success; this does not close the remaining manual/operational gates |
| core-gates | [41288774875](https://github.com/butnee-sys/gerchain/actions/runs/41288774875) | **PENDING**; no jobs returned and no artifact. This is an open CI/release-governance item |

The PostgreSQL lifecycle report records:
- `commit_sha == checked_out_head_sha == tested_commit == e543ba112ff2c311b50ec7b7a8697b326e6d6b23`;
- `evidence_status = PASS_CANDIDATE`;
- `source_hashes_complete = true`, 13 source files, no missing source files, clean source worktree;
- all 17 migration file SHA-256 values match their applied migration history;
- migration versions 001–017 exactly;
- lifecycle JUnit: 6 tests, 0 failures, 0 errors, 0 skipped.

The separate PostgreSQL production re-performance artifact also binds `github_sha == checked_out_sha == e543ba112ff2c311b50ec7b7a8697b326e6d6b23`, reports 17 migration versions, validated escrow constraints, production boot PASS, and 25/25 PostgreSQL tests passed. Its reconciliation is explicitly an **empty-baseline** check (zero movements/witness/outbox/idempotency/escrow rows); it is not a populated production transaction graph.

## 2. Historical 21-failure disposition at this candidate

Original diagnostic: run 39849400091 / artifact 12456921635 at `d9c8af8...`, 21 failed, 899 passed, 50 skipped. These failures are not to be erased from history.

At candidate `e543ba112ff2c311b50ec7b7a8697b326e6d6b23`:
- Rows #2–#21: all 20 exact historical SHUUD test cases appear in the dedicated Product MVP JUnit and individually PASS. Artifact 13076670356; 108 tests total, 0 failures/errors/skips.
- Row #1, `test_shuud_workflows_are_path_isolated`, is superseded by the updated contract `test_shuud_workflows_are_separate_manual_entrypoints`. The Production Gate per-file JUnit at artifact 13076497382 records five `tests.test_final_lock_contract` cases, all passing, including the replacement contract. This is a justified contract correction/replacement, not a claim that the old assertion ran unchanged.
- Scope: SHUUD/SANDBOX remain separate product MVPs, not EAI acceptance components. Product pass results are recorded separately and do not certify a SHUUD production deployment.

Therefore, the 21 historical failures have current same-SHA test-level evidence: #2–#21 re-passed; #1's revised contract passed. Preserve their original causes and this superseding evidence in the row register. Do not state that the original 21-failure run itself was fixed retroactively.

## 3. Eighteen skipped tests — classification

The Production Gate segmented EAI diagnostic JUnit records 18 skips, all caused by missing environment variables, not assertion failures:

| Group | Count | Missing configuration | Disposition |
|---|---:|---|---|
| Production lifecycle/full-flow tests | 2 | `GERCHAIN_TEST_POSTGRES_URL`, `TEST_POSTGRES_URL` | Not exercised in this diagnostic; dedicated PostgreSQL lifecycle/re-performance gates provide related but not identical evidence |
| PostgreSQL migration concurrency / bootstrap / rollback / checksum / constraint cases | 14 | `GERCHAIN_TEST_POSTGRES_URL` | Not exercised in this diagnostic; clean PostgreSQL migration and concurrency gates passed, including 25-test PostgreSQL re-performance. Keep individual skipped tests distinct unless their exact node IDs are run in a configured job |
| Production entrypoint PostgreSQL boot | 1 | `GERCHAIN_TEST_PRODUCTION_DATABASE_URL` | Not exercised in this diagnostic; dedicated production PostgreSQL boot evidence passed |
| DEE persistent registry concurrent rotation | 1 | `DEE_POSTGRES_URL` | **OPEN / NOT VERIFIED**; no equivalent same-SHA dedicated result identified in the retained artifacts |

The 18 are not PASS and are not failures. The PostgreSQL-specific skipped tests have overlapping dedicated-gate evidence, but not every skipped node ID is proven to have executed. The DEE concurrent-rotation case remains a clear gap.

## 4. MG-07 through MG-14

| Gate | Current evidence at `e543ba112ff2c311b50ec7b7a8697b326e6d6b23` | Disposition |
|---|---|---|
| MG-07 Legacy authority freeze | Canonical Ledger authority and legacy endpoint shutdown are documented; EA34 record explicitly says legacy tables are not physically read-only/removed | **OPEN** — require physical write-freeze proof, production route write-denial and negative tests |
| MG-08 IAM/MFA and privileged access | No current identity-provider export, MFA enforcement evidence, privileged-user review, least-privilege/revocation test or independent attestation in this evidence set | **OPEN** |
| MG-09 Observability and operational recovery | Runtime boot and restart/recovery-oriented tests exist; no complete production telemetry/alert exercise, incident response, and no-duplicate-movement operational drill retained | **OPEN** |
| MG-10 Performance and concurrency | PostgreSQL concurrency/replay tests passed; no approved production-like workload, throughput/latency/error thresholds, capacity envelope and raw load report identified | **PARTIAL / OPEN** |
| MG-11 Backup/restore and DR | No backup restore drill, post-restore reconciliation, RPO/RTO measurements or failover evidence identified | **OPEN** |
| MG-12 CI/release governance | Multiple exact-SHA workflows passed; `core-gates` is pending. Branch-protection/ruleset state could not be read through the available GitHub permission, so protected-branch enforcement is not verified | **OPEN** |
| MG-13 Independent re-performance | Automated Independent Production Audit passed, but its own verdict disclaims production certification; no named independent reviewer sign-off or independently controlled re-performance attestation is present | **PARTIAL / OPEN** |
| MG-14 Evidence index and authorized approval | Artifacts are linked above, but no complete signed evidence index and no explicit authorized final-lock decision exist | **OPEN** |

## 5. SHA discrepancy disposition

The historical artifact 12457545216 from run 39849400050 remains quarantined: it embedded `e872ba14...` while the run head was `d9c8af8...`. It is not rewritten or accepted.

The replacement artifact 13076387227 from run 41288774805 correctly binds run 41288774805 and candidate `e543ba112ff2c311b50ec7b7a8697b326e6d6b23` in both GitHub metadata and the embedded `github_sha` / `checked_out_sha` fields. The old artifact remains invalid for its claimed run; the new artifact is admissible only for this candidate and only at `PASS_CANDIDATE` level.

## 6. Required next actions

1. Resolve why `core-gates` run 41288774875 is pending; obtain completed job logs and retained JUnit at a frozen candidate SHA.
2. Execute the DEE concurrent-rotation test with a configured PostgreSQL service and retain its exact-SHA JUnit/log.
3. Complete MG-07 physical write freeze, MG-08 IAM/MFA, MG-09 observability/recovery, MG-10 production-like load, MG-11 backup/restore/DR, MG-12 branch/release protection, MG-13 independent reviewer re-performance, and MG-14 authorized evidence acceptance.
4. Create one final evidence index mapping every required control and artifact to the final SHA and deployment identity.
5. Freeze that final SHA and rerun every mandatory code, workflow, migration, PostgreSQL, product-scope, security and independent gate against it. Any later relevant change requires a new candidate and re-performance.

**No final lock is granted by this audit.**
