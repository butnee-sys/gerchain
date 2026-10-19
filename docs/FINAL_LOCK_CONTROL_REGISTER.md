# FINAL LOCK Control Register

Status: ACTIVE CONTROL / FINAL LOCK NOT YET DECLARED
Repository: butnee-sys/gerchain
Working branch: feat/ea21-transaction-aware-ledger
Last reviewed branch commit: 4fd6b3b18a552e9d8a5d217953685751ed6d250f
Purpose: drive the fundamental architecture and EAI to a defensible FINAL LOCK without reopening already-closed findings without new evidence.

## 1. Mission and completion rule

The objective is FINAL LOCK of the fundamental architecture and EAI. Inspection, tests, audits, and repairs are means to that end, not the objective. Work must be organized around closing the remaining release gates, not generating repeated findings.

A lock decision must be explicit and based on evidence tied to the exact final commit. A finding-free report by itself is not a lock.

## 2. Anti-recurrence protocol

Every finding must have a stable ID and exactly one status:
- OPEN: a demonstrated, currently applicable blocker.
- IN_PROGRESS: a specific repair is being implemented.
- VERIFY: repair exists and awaits evidence against the exact candidate commit.
- CLOSED: repair and required evidence passed on the recorded commit.
- ACCEPTED_RISK: explicitly approved by the authorized owner with scope and expiry/conditions.
- REOPENED: allowed only when new evidence disproves the prior closure, the relevant code/schema changed, or a reproducible regression is observed.

Each register entry records: ID, claim, affected boundary, first evidence, fix commit, verification commit/run, result, status, and closure date.

### No-repeat rule
Before reporting any issue, compare it against this register and prior evidence. If the same issue is CLOSED and there is no new counter-evidence, do not report it as a new issue. Reference the existing ID and closure evidence. If the latest candidate commit differs from the verified commit, run only the relevant regression check; do not reset the finding to OPEN merely because the SHA changed.

No status may be inferred from memory or a previous narrative. Link to the source file, commit, CI run, or test result.

## 3. Evidence levels

- IMPLEMENTED: code/configuration exists; runtime proof is not implied.
- TESTED: a named test passed.
- CI-VERIFIED: the required workflow succeeded on the exact candidate commit.
- POSTGRES-REPERFORMED: real PostgreSQL service and production path passed on the exact candidate commit.
- INDEPENDENTLY-REPERFORMED: a separate reviewer/process repeated the required proof.
- LOCKED: every mandatory release gate is closed or explicitly accepted by the authorized owner, the exact final commit is recorded, and a lock decision is documented.

An empty status/check list means UNVERIFIED, not success and not failure.

## 4. Known evidence; do not rediscover without contradiction

- Canonical architecture freeze: docs/DEE_ARCHITECTURE_FREEZE.md, frozen 2026-09-14, blob 0940d8aae8858d34604eb9d7174a8afc636bb2f.
- Canonical PostgreSQL production runtime and schema guard are implemented in services/gerchain_runtime_factory.py and production_entrypoint.py. This is implementation evidence only until exact-tip CI and PostgreSQL re-performance are attached.
- docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md records successful PostgreSQL 16 evidence for exact execution SHA 890a78f36dcfe161e195da649b3cd124133d6535 (runs 36317914217, 36317914351, 36317914313, 36317914446, 36317914344, 36317914254, 36317914266) and later exact-SHA evidence for f158316277d65234e355b6040a905884ee4f4adf (run 37002917360). These are historical evidence; they must not be represented as verification of a newer commit.
- The 2026-10-18 CI change at 4fd6b3b18a552e9d8a5d217953685751ed6d250f adds Canonical Ledger transaction-boundary and deep value-truth tests to ci.yml. Exact-tip workflow status must still be retrieved before calling this commit CI-VERIFIED.
- Existing architecture and EAI definitions are frozen; no new layer or second authoritative Ledger, Escrow Engine, Witness Chain, or outbox may be introduced to simplify closure.

## 5. Final Lock gates

| Gate | Required closure evidence | Status at register creation |
|---|---|---|
| G1 Canonical architecture | Frozen document unchanged or approved architecture-change record | FROZEN baseline exists; final diff check required |
| G2 Canonical Ledger / value authority | All production value mutations use one transaction-aware Ledger boundary | IMPLEMENTED; exact-tip CI proof pending |
| G3 Escrow lifecycle / durable truth | CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, READ, SETTLEMENT tested against PostgreSQL | Historical PostgreSQL evidence exists; exact-tip proof pending |
| G4 Cross-store value truth | Deep reconciliation links movement, escrow, witness, outbox, idempotency and integrity hash | Tests added to CI; exact-tip result pending |
| G5 Migration and schema | Ordered migration history, exact schema constraints, no unexplained drift | Schema guard implemented; exact-tip PostgreSQL proof pending |
| G6 Production entrypoint | Boot uses PostgreSQL and canonical authority; fail-closed on invalid configuration/schema | Implemented; exact-tip boot proof pending |
| G7 Legacy authority freeze | Legacy balance/value stores cannot mutate production truth; removal/archive decision recorded | OPEN pending evidence |
| G8 Security governance | IAM/MFA and privileged access evidence, or explicitly approved risk acceptance | OPEN pending owner-approved evidence |
| G9 CI / branch governance | Required checks succeed on exact candidate commit; merge/branch rules evidenced | UNVERIFIED |
| G10 Independent re-performance | Separate reproducible proof package for the final candidate | OPEN |
| G11 Final decision | All mandatory gates closed/accepted, final SHA and evidence index recorded, explicit FINAL LOCK | NOT LOCKED |

## 6. Execution order from here

1. Retrieve and record exact candidate commit and its CI runs.
2. Close exact-tip CI failures once, recording their stable finding IDs.
3. Run the PostgreSQL production re-performance gate on that exact candidate; preserve logs/artifacts.
4. Resolve only gates still OPEN: legacy-store freeze/removal, security governance, branch governance, independent re-performance.
5. Re-run only the impacted regression suites after each repair; preserve previously closed findings.
6. Produce a single final evidence index with every gate and source link.
7. Issue FINAL LOCK only after the release criteria above are satisfied. Do not extend scope into product layers before this lock.

## 7. Reporting format

Every continuation report must begin with:
- Objective: FINAL LOCK
- Current candidate SHA
- Closed since last report (with evidence)
- Remaining blockers only (stable IDs)
- Next action that closes a blocker

Do not repeat the entire audit. Do not report closed findings as newly discovered. Do not say GREEN when evidence is absent. Do not stop at “NOT LOCKED”: continue executing the next closure action.
