# EA-35 / EAI-CORE — Alternative Verification Gate Strategy

Status: DECISION APPROVED FOR IMPLEMENTATION; NOT YET VERIFIED
Date: 2026-10-10

## Problem statement

The two observed GitHub Actions runs are both queued:
- FINAL EAI/CORE Exact-SHA Gate: 38044794837
- EA-35 PostgreSQL Re-performance: 38044791836

The currently available evidence proves only that the jobs have not started. It does not prove a code failure, a PostgreSQL failure, or a successful gate. Repeatedly editing application code while jobs remain queued is not an evidence-based response.

## Decision: stop the retry-and-edit loop

Do not start additional duplicate runs and do not label either existing run green. First collect runner/workflow/job evidence. If the jobs remain queued, treat this as an execution-plane blockage until proven otherwise, not as an application-code defect.

## New approach: one orchestrated, exact-SHA gate

Replace the two independent release-decision paths with one sequential orchestration workflow. Keep test scopes separate as steps/jobs inside that orchestration, but expose one final verdict.

Required workflow inputs:
- target_sha: full 40-character commit SHA (required; never infer from branch tip)
- mode: preflight | full
- run_postgres: boolean; full mode requires true

Required phases, in order:
1. Preflight: verify target SHA exists, checkout exactly that SHA, print SHA and workflow/run metadata, verify required secrets and PostgreSQL service configuration are present without printing secret values.
2. Static/contract phase: validate canonical architecture and migration contract; run fast unit tests.
3. PostgreSQL phase: start a known PostgreSQL service, wait for pg_isready, apply explicit migrations, report schema version, run targeted integration tests.
4. EAI/CORE phase: run EAI/CORE checks against the same target SHA and same database/schema version where appropriate.
5. Deep value-truth phase: run cross-store reconciliation and assert no unexplained movement/witness/outbox/idempotency/integrity discrepancies.
6. Final evidence: emit one machine-readable summary with target SHA, run ID, job conclusions, PostgreSQL version, migration/schema version, test counts, and explicit blockers.
7. Verdict: PASS only if every required phase completed on the exact SHA. QUEUED, skipped, missing evidence, service unavailable, timeout, or unknown status means NOT VERIFIED, never PASS.

## Execution-plane safeguards

- Add explicit job-level timeouts so a started-but-stuck job fails with diagnostic evidence.
- Use one concurrency group for the unified gate to prevent duplicate gate runs competing with each other; do not cancel a valid run without recording why.
- Keep PostgreSQL as a declared service dependency and include a readiness loop with bounded timeout and logs.
- On queue, inspect repository Actions permissions, runner availability, required environment approvals, concurrency locks, and job dependencies before touching application code.
- Never use continue-on-error for required checks.
- Never let a successful static job imply PostgreSQL or full production readiness.
- Keep a failed/blocked stage's logs and summary as artifacts; final status must identify the first blocking phase and later phases not run.

## Acceptance criteria

The alternative is accepted only when:
- A single run starts and checks out the exact requested SHA.
- All required jobs reach terminal conclusions.
- PostgreSQL readiness and migration are explicitly evidenced.
- EAI/CORE and EA-35 tests run, not skipped.
- The deep reconciliation result is captured.
- A final summary identifies the same SHA across all phases.
- A fresh exact-SHA run passes; otherwise the gate remains NOT VERIFIED.

## Current status

IN PROGRESS / NOT LOCKED. Existing run IDs remain evidence of a queued state only. No claim of production readiness is authorized from these runs.