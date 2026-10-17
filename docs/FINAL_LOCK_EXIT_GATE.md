# FINAL LOCK Exit Gate — Recurrence Control

Status: ACTIVE CONTROL POLICY / NOT A PRODUCTION ATTESTATION
Scope: Canonical CORE PostgreSQL authority and the SHUUD boundary. This document prevents already-accepted evidence from being repeatedly reopened without a new, concrete regression.

## 1. Objective

Stop the loop of detect → fix → detect when the new finding is only a renamed symptom, duplicate report, or previously accepted condition. Preserve existing verification evidence and focus only on deltas.

## 2. Evidence reuse

Previously accepted test results, audit records, CI records, and architecture decisions remain accepted unless one of these triggers is present:
- a new commit changes the verified code or its dependency/configuration boundary;
- a previously passing test now fails on the relevant commit;
- a concrete production incident or reproducible failure contradicts the evidence;
- a frozen invariant is demonstrably violated;
- the earlier evidence is shown to have used the wrong runtime, database, schema, branch, or configuration.

A request for another full review, a renamed finding, or the mere passage of time is not by itself a reopen trigger.

## 3. Finding identity and deduplication

Every finding must have:
- stable finding ID;
- affected component and exact file/line or runtime boundary;
- observable failure and reproduction evidence;
- root cause (not symptom only);
- linked fix commit;
- regression test or explicit reason why a regression test is not applicable;
- closure evidence.

If a new report has the same root cause and same invariant as an open finding, attach it to that finding. Do not create a second repair track.

## 4. CORE PostgreSQL guard

Before reopening the CORE PostgreSQL track, identify which concrete class applies:
1. wrong database/runtime selected;
2. schema or migration mismatch;
3. transaction/locking/idempotency defect;
4. configuration or environment mismatch;
5. genuine code regression.

Do not treat these classes as interchangeable. A test-memory or SQLite result cannot contradict PostgreSQL-specific evidence unless it demonstrates a shared-code regression. Conversely, PostgreSQL-specific behavior must be tested against the PostgreSQL path when a new concrete failure is reported.

## 5. SHUUD boundary guard

A SHUUD finding reopens the locked foundation only when evidence shows it bypasses or mutates a protected canonical boundary, breaks a required adapter contract, or regresses an already accepted SHUUD invariant. Product/API symptoms that do not violate a foundation invariant remain in the SHUUD workstream and must not automatically reopen CORE or EAI.

## 6. Change-scope verification

For each fix, verify only:
- the reported failure;
- the exact invariant it could affect;
- directly dependent interfaces and transaction boundaries;
- the regression test that prevents recurrence.

Do not repeat the entire audit suite unless the change affects a shared authority, schema, transaction boundary, canonical adapter, or production runtime selection.

## 7. FINAL LOCK decision

A component can be marked LOCKED when:
- its previously accepted evidence is indexed and linked;
- no unresolved finding demonstrates a frozen-invariant violation;
- new findings have stable IDs and root-cause deduplication;
- all changes since the accepted baseline have scoped regression evidence;
- known limitations are explicitly recorded rather than endlessly reopened.

An unrelated open item does not block a component lock unless a documented dependency or invariant connects them.

## 8. Status vocabulary

- IMPLEMENTED: code or policy exists.
- VERIFIED: evidence for the stated scope exists and is linked.
- OPEN: a concrete unresolved finding exists.
- UNVERIFIED: evidence has not been retrieved or confirmed for the exact ref.
- LOCKED: the stated scope passed its exit gate and is not reopened without a defined trigger.

Do not label a status GREEN/LOCKED based only on this policy document. This document changes the process for evaluating evidence; it does not substitute for technical evidence.

## 9. Required finding format

`ID | component | invariant | reproduction/evidence | root cause | fix commit | regression proof | status`

If the root cause is not yet known, label it ROOT-CAUSE-OPEN and do not produce speculative duplicate fixes.
