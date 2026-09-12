# SHUUD Sandbox Incident Scenarios

| ID | Scenario | Expected path | Primary KPI |
|---|---|---|---|
| S1 | Eligible minor incident | Full rapid path | Clearance seconds |
| S2 | Evidence capture delay | Complete with measured delay | Evidence-to-verification seconds |
| S3 | Verification rejection | Stop rapid path safely | Rejection + audit completeness |
| S4 | SHIID rejection | No release; escalate | Decision latency |
| S5 | Process restart before release | Recover and continue | Recovery success |
| S6 | Concurrent release | One winner only | CAS conflict correctness |
| S7 | Settlement delay | Clear first, settle later | Clearance-to-settlement |
| S8 | Out-of-scope incident | Conventional escalation | Correct exclusion |
| S9 | Missing evidence | Reject/hold | Evidence completeness |
| S10 | Duplicate request | Idempotent handling | Duplicate protection |

## Common evidence requirements

Each sandbox case should retain an incident identifier, evidence reference, verification result, SHIID decision, clearance confirmation, escrow state, settlement result and measurement summary.

## Reporting rule

A scenario that is intentionally outside the rapid-path eligibility rules is not a failed rapid-path case. It is a routing-control test.

## Benchmark rule

The 120-second objective is evaluated on eligible rapid-path cases only. Report median, P90 and share completed within 120 seconds; do not report a mean alone.
