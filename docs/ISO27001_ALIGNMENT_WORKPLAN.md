# MNS ISO/IEC 27001:2023 — GerChain CORE Alignment Workplan

**Version:** 0.1  
**Status:** Controlled workplan  
**Technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## Objective

Build an evidence-based ISMS alignment package around the frozen GerChain CORE technical baseline without changing the CORE implementation merely to create documentation evidence.

## Work sequence

### Phase 0 — Freeze and evidence preservation
- Confirm baseline SHA.
- Preserve existing CORE evidence.
- Confirm SHUUD remains outside CORE assurance scope.
- Establish document/version control.

**Gate:** baseline immutable.

### Phase 1 — ISMS scope and context
- ISMS scope.
- Organizational context.
- Interested parties and requirements.
- Organizational/security roles.
- Interfaces with third parties.

**Gate G1:** scope formally reviewed.

### Phase 2 — Information assets and classification
- Information asset register.
- Asset owners.
- Information classification.
- Handling, storage, transfer and disposal requirements.

**Gate G2:** all scoped critical information assets identified and owned.

### Phase 3 — Risk management
- Risk methodology.
- Threat/vulnerability identification.
- Likelihood and impact.
- Risk treatment.
- Risk acceptance authority.

**Gate G3:** risk register and treatment plan approved.

### Phase 4 — Statement of Applicability
- Map risk treatment to applicable controls.
- Assess Annex A controls for applicability.
- Record justification for exclusions.
- Record implementation status and evidence.

**Gate G4:** SoA complete and traceable.

### Phase 5 — Control implementation and organizational evidence
Priority controls:
- identity and access management;
- MFA;
- privileged access;
- cryptographic key management;
- secure development;
- change/release management;
- logging and monitoring;
- backup/recovery;
- incident management;
- supplier security;
- human-resource security;
- physical security;
- business continuity;
- compliance and records management.

**Gate G5:** required controls have objective evidence.

### Phase 6 — Evidence system
Create one evidence register linking:

`Requirement → Risk → Control → Implementation → Evidence → Owner → Review date → Status`

Evidence shall be versioned and traceable to the relevant system/configuration/repository state.

**Gate G6:** evidence completeness reviewed.

### Phase 7 — Internal audit
- Audit plan.
- Control sampling.
- Evidence verification.
- Nonconformity register.
- Corrective actions.
- Follow-up verification.

**Gate G7:** internal audit completed.

### Phase 8 — Management review
Management shall review ISMS performance, risks, incidents, audit results, objectives, resources and improvement actions.

**Gate G8:** management review completed and recorded.

### Phase 9 — Independent assessment readiness
- Independent re-performance of selected technical controls.
- Verification of organizational IAM/MFA evidence.
- Verification of privileged access governance.
- Verification of evidence integrity and traceability.
- Final gap assessment.

**Gate G9:** no unresolved certification-blocking gaps.

### Phase 10 — Certification assessment
Only after the preceding gates are satisfied should formal certification assessment be commissioned.

## Non-negotiable rules

1. Do not claim certification before certification is actually granted.
2. Do not mark a control GREEN without objective retained evidence.
3. Do not treat a software test as proof of an organizational policy.
4. Do not place secrets, private keys, passwords or production credentials in the repository.
5. Do not alter the frozen CORE baseline solely to satisfy paperwork.
6. Keep SHUUD outside CORE assurance scope unless the scope is formally expanded.
7. Every final conclusion must identify its evidence and audited baseline.

## Current known gaps

- Organizational IAM/MFA evidence: MISSING.
- Privileged access evidence: MISSING.
- Independent re-performance: OPEN.
- Formal ISMS scope approval: OPEN.
- SoA: not yet completed.
- Full risk register: not yet completed.
- Internal audit: not yet completed.
- Management review: not yet completed.

## Status

**Overall MNS ISO/IEC 27001:2023 alignment: IN PROGRESS — not certified.**
