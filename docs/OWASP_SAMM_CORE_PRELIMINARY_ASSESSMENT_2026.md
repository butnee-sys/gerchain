# OWASP SAMM v2 — GerChain CORE Preliminary Assessment

**Assessment type:** preliminary evidence-based self-assessment
**Scope:** GerChain CORE only
**SHUUD:** OUT OF SCOPE / frozen
**Candidate technical baseline:** `7f051b4dc742553198173f551196ca9d43e757fd`
**Date:** 2026-09-15

This document is a preliminary mapping of currently available GerChain CORE evidence against OWASP SAMM v2. It is not an OWASP-certified assessment, independent audit, or certification.

OWASP SAMM defines five business functions and fifteen security practices, each with three maturity levels. The official SAMM assessment toolbox evaluates activities against defined quality criteria and calculates a maturity score. This document deliberately does **not** invent SAMM scores where organizational evidence is incomplete.

## Evidence basis

- PostgreSQL transaction/concurrency assurance
- CORE Operating Reconciliation
- core-gates CI
- CodeQL Advanced
- Trivy CORE container scan: 0 Critical / 0 High / 0 Medium at the candidate baseline
- Snyk PR security check
- OSV-Scanner dependency scan
- idempotency and replay controls
- outbox/recovery/reconciliation controls
- cryptographic/decision controls
- repository governance and protected-main controls
- CORE audit/evidence documentation
- independent-review request in GitHub Issue #74

Organizational evidence such as IAM/MFA operation, privileged-access records, management review, personnel security, supplier controls, and independent audit evidence is not inferred from source code.

## Preliminary practice mapping

| SAMM business function | Security practice | Preliminary status | Evidence position |
|---|---|---|---|
| Governance | Strategy & Metrics | PARTIAL | CORE assurance gates and evidence tracking exist; formal organization-wide metrics program not fully evidenced |
| Governance | Policy & Compliance | PARTIAL | ISO/IEC 27001 alignment documents and control mapping exist; organizational operation/certification not evidenced |
| Governance | Education & Guidance | OPEN | No sufficient objective evidence of organization-wide security education/training program |
| Design | Threat Assessment | PARTIAL | Security architecture, risk treatment, control boundaries and external security scanning exist; formal SAMM threat-assessment process not fully evidenced |
| Design | Security Requirements | PARTIAL | Security/runtime requirements and acceptance gates exist; complete lifecycle requirements process not independently evidenced |
| Design | Secure Architecture | PARTIAL/GREEN TECHNICAL | CORE architecture, Money Ledger/Engine, Escrow Engine, Witness Chain, reconciliation and trust boundaries are documented; independent architecture assessment remains pending |
| Implementation | Secure Build | GREEN TECHNICAL / PARTIAL MATURITY | Protected main, required CI gates, CodeQL, Scorecard work, Trivy, Snyk and OSV evidence exist; organizational maturity evidence remains incomplete |
| Implementation | Secure Deployment | PARTIAL | CI/CD governance and protected-main controls exist; production deployment controls and operational evidence are incomplete |
| Implementation | Defect Management | PARTIAL | Findings are tracked and remediation evidence is being retained; formal enterprise defect-management lifecycle is not fully evidenced |
| Verification | Architecture Assessment | OPEN / PENDING INDEPENDENT | Internal architecture evidence exists; independent technical re-performance is still pending |
| Verification | Requirements-driven Testing | GREEN TECHNICAL / PARTIAL MATURITY | CORE gates, PostgreSQL concurrency, reconciliation and transaction tests are evidenced; full requirements-to-test traceability is incomplete |
| Verification | Security Testing | GREEN TECHNICAL / PARTIAL MATURITY | CodeQL, Trivy, Snyk and OSV provide multiple automated security evidence sources; Codex Security scan unavailable due to usage limit; independent testing pending |
| Operations | Incident Management | OPEN | Incident-response requirements/evidence templates exist, but operational incident-management evidence is incomplete |
| Operations | Environment Management | PARTIAL | Container hardening/remediation and dependency scanning are active; full environment baseline/monitoring lifecycle not evidenced |
| Operations | Operational Management | PARTIAL | Reconciliation, recovery and audit controls exist; full operational governance and management-review evidence is incomplete |

## Preliminary maturity interpretation

The current evidence supports the following **non-certifying** conclusion:

- **Technical software assurance:** substantially established for the CORE candidate.
- **Process maturity:** partially established.
- **Organizational security maturity:** insufficient evidence for a high maturity claim.
- **Independent verification:** pending.
- **OWASP SAMM formal score:** NOT CLAIMED until the official SAMM assessment questions and quality criteria are completed with the responsible stakeholders.

The strongest currently evidenced SAMM areas are Secure Build, Requirements-driven Testing, Security Testing, Secure Architecture, and Environment Management.

The principal maturity gaps are Governance evidence, Education & Guidance, formal threat-assessment process, Secure Deployment operational evidence, Defect Management lifecycle evidence, independent Architecture Assessment, Incident Management operation, and Operational Management/management review.

## Next assessment step

Use the official OWASP SAMM Assessment Toolbox to answer every activity question and quality criterion with responsible stakeholders. Where a criterion is not completely fulfilled, record it as not fulfilled rather than awarding inferred credit.

The resulting SAMM score should then be stored separately from this preliminary mapping and labelled **self-assessment**.

## Assurance wording

> “GerChain CORE-ийн software assurance maturity-г OWASP SAMM v2-ийн хүрээнд урьдчилан үнэлэхэд техникийн security assurance-ийн суурь бүрдсэн боловч байгууллагын процесс, үйл ажиллагаа болон хараат бус баталгаажуулалтын нотолгоо бүрэн болоогүй байна. Иймд одоогоор SAMM-ийн албан ёсны maturity score болон certification claim гаргаагүй.”

**SHUUD is excluded from this assessment.**
