# SHUUD — Assurance Evidence Register

## Status model

- GREEN = verified evidence satisfies the defined acceptance criterion.
- PARTIAL = evidence exists but is incomplete.
- OPEN = evidence not yet collected or independently verified.
- FAIL = acceptance criterion not satisfied.
- N/A = formally excluded from the SHUUD release scope.

## Evidence register

| ID | Area | Evidence required | Status |
|---|---|---|---|
| SHUUD-SEC-001 | Authentication | Authenticated access and role separation test | OPEN |
| SHUUD-SEC-002 | Authorization | Unauthorized action rejection test | OPEN |
| SHUUD-SEC-003 | Input security | Malformed/untrusted input rejection | OPEN |
| SHUUD-SEC-004 | Secrets | No secret exposure in code/config/build artifacts | OPEN |
| SHUUD-SEC-005 | Dependencies | Dependency vulnerability inventory | OPEN |
| SHUUD-FUN-001 | Core flow | Valid SHUUD case completes expected flow | OPEN |
| SHUUD-FUN-002 | Evidence | Required evidence is persisted and traceable | OPEN |
| SHUUD-FUN-003 | Decision | Decision is reproducible from recorded evidence | OPEN |
| SHUUD-FUN-004 | Release/payment | Release occurs only after required conditions | OPEN |
| SHUUD-INT-001 | CORE boundary | CORE API contract test | OPEN |
| SHUUD-INT-002 | Idempotency | Retry does not duplicate release/payment | OPEN |
| SHUUD-INT-003 | Failure recovery | Integration failure recovery test | OPEN |
| SHUUD-PERF-001 | Response time | Defined pilot response-time target | OPEN |
| SHUUD-PERF-002 | Load | Pilot load/concurrency test | OPEN |
| SHUUD-OPS-001 | Availability | Pilot availability evidence | OPEN |
| SHUUD-OPS-002 | Recovery | Operational recovery evidence | OPEN |
| SHUUD-ASSURE-001 | Re-performance | Independent technical re-performance | OPEN |

## Acceptance rule

No SHUUD item is marked GREEN merely because the corresponding CORE control is GREEN. SHUUD must produce its own product-level evidence.

## Boundary rule

If an evidence result identifies a suspected CORE defect, the finding is escalated to the CORE change/assurance process. Until that review is completed, the finding remains a SHUUD-level finding.
