# PRODUCTION READY — Evidence-Based Readiness Scorecard

**Assessment date:** 2026-10-19  
**Repository:** `butnee-sys/gerchain`  
**Branch under assessment:** `feat/ea21-transaction-aware-ledger`  
**Assessment status:** PRELIMINARY BASELINE — NOT A CERTIFICATE  
**Release status:** IN PROGRESS / NOT LOCKED

## 1. Purpose

This scorecard prevents implementation activity from being confused with verified production readiness. The percentage is a weighted evidence score, not a subjective estimate of lines of code or effort.

A gate earns points only for evidence that exists and is inspectable. Historical success on an earlier commit earns partial credit where the current exact commit has not been re-performed. Unknown or missing evidence earns zero; it is not treated as a pass.

## 2. Readiness score

| Gate | Weight | Earned | Basis |
|---|---:|---:|---|
| Frozen canonical architecture and invariants | 10 | 10 | Canonical freeze document exists; architectural boundaries and single-authority invariants are documented. |
| Canonical value-flow implementation | 20 | 16 | Runtime paths for FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, account creation and balance reads are implemented against Canonical Ledger / durable Escrow boundaries. Full current-SHA verification remains outstanding. |
| PostgreSQL production execution | 15 | 10 | Repository evidence records successful PostgreSQL 16 production re-performance runs on execution SHA `890a78f36dcfe161e195da649b3cd124133d6535` (workflow runs listed in EA34 audit). This is historical evidence, not proof for today's branch tip. |
| Versioned migration and schema guard | 10 | 7 | Factory includes migration registry execution and canonical schema assertions. Fresh run on current exact SHA and clean-database migration proof still required. |
| Deep value-truth reconciliation | 10 | 7 | Reconciliation implementation and negative/integration tests exist for movement, escrow, witness, outbox, idempotency and integrity links. Current exact-SHA CI and real-PostgreSQL re-performance are not established in this assessment. |
| Exact-SHA CI/reproducibility | 10 | 3 | Earlier workflow successes are recorded, but no fresh complete successful CI evidence has been attached to the assessed current tip in this scorecard. |
| Identity, privileged access, MFA and governance | 5 | 0 | Prior control/evidence register marks IAM/MFA and privileged-access review as missing or open. |
| Legacy authority freeze/removal proof | 5 | 2 | Legacy mutation routes were made fail-closed and a freeze document exists; physical removal/archive and complete read-only proof remain open. |
| Operations: readiness, observability, backup/DR and recovery | 5 | 1 | Entrypoint has fail-closed boot checks and connection probe; operational SLO, alerting, backup/restore and DR proof are not closed here. |
| Independent re-performance / final assurance | 10 | 0 | Independent evidence package and independent oracle sign-off remain open. |
| **TOTAL** | **100** | **56** | **PRELIMINARY EVIDENCE SCORE** |

## 3. What 56% means — and does not mean

**56% is the current evidence-based planning baseline, not a claim that the software is 56% coded or that it is safe to deploy.** The score deliberately penalizes missing current-commit proof, organizational controls, operations, and independent assurance.

The earlier PostgreSQL run records are useful evidence, but their execution SHA differs from the present branch work. They cannot be silently promoted to current-SHA proof.

## 4. Production certificate gates

The certificate must not be issued until all mandatory release gates are closed, regardless of the weighted score:

1. Exact release commit SHA is frozen.
2. Clean PostgreSQL database migration completes from zero without manual repair.
3. Canonical schema constraints and migration history are verified.
4. Production entrypoint boots against that database and fails closed on invalid configuration/schema.
5. FUND / LOCK / RELEASE / REFUND / CANCEL / SETTLEMENT / READ are exercised against PostgreSQL.
6. Replay, conflicting idempotency, rollback, concurrent requests, restart/recovery and failure paths pass.
7. Deep value-truth reconciliation reports no unexplained issue.
8. Legacy balance/value authorities are proven non-authoritative and unable to mutate production value.
9. Exact-SHA CI is fully successful and artifacts/logs are retained.
10. IAM/MFA, privileged access, monitoring, backup/restore and DR controls are evidenced or explicitly accepted by the accountable authority.
11. Independent re-performance is completed.
12. Certificate names the exact commit SHA, test environment, evidence references, residual risks and sign-off authority.

## 5. Score update rule

For each gate, record:
- weight;
- earned points;
- status: `MISSING`, `IMPLEMENTED`, `VERIFIED ON HISTORICAL SHA`, `VERIFIED ON RELEASE SHA`, or `ACCEPTED RISK`;
- evidence URL/artifact;
- exact commit SHA;
- verifier and date;
- remaining action.

Only `VERIFIED ON RELEASE SHA` or a documented, accountable `ACCEPTED RISK` may receive full release-gate credit. An implementation commit alone is not verification.

Recalculate as:

`Readiness % = sum(earned gate points) / 100 × 100`

Do not change weights or backfill evidence silently. Any scoring-model change must be versioned and the old score retained for comparison.

## 6. Immediate next actions

1. Resolve all production factory/entrypoint signature and schema-bootstrap consistency issues on one exact commit.
2. Run the clean PostgreSQL migration + production smoke + full value-flow + deep reconciliation workflows on that exact commit.
3. Inspect workflow jobs and artifacts; record actual run IDs and outcomes in this scorecard.
4. Close or explicitly risk-accept IAM/MFA and legacy authority freeze/removal.
5. Run independent re-performance.
6. Recalculate the score from evidence and issue the certificate only after mandatory gates close.

## 7. Current decision

**NO PRODUCTION READY CERTIFICATE ISSUED.**

Reason: the repository contains substantial implementation and historical PostgreSQL execution evidence, but current exact-SHA CI/re-performance, organizational security controls, operational recovery/DR evidence and independent assurance are not all closed in this assessment.

This scorecard is a working control document. It is not an external audit opinion, regulatory approval, penetration-test attestation, or guarantee of fitness for every deployment.
