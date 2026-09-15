# OWASP SAMM v2 — GerChain CORE Preliminary Assessment

**Assessment type:** preliminary evidence-based self-assessment mapping
**Scope:** GerChain CORE only
**SHUUD:** OUT OF SCOPE / frozen
**Candidate technical baseline:** `7f051b4dc742553198173f551196ca9d43e757fd`
**Date:** 2026-09-15

This document is a preliminary mapping of currently available GerChain CORE evidence against OWASP SAMM v2. It is **not** an OWASP-certified assessment, independent audit, or certification.

OWASP SAMM v2 defines five business functions and fifteen security practices, with three maturity levels for each practice. The official assessment toolbox evaluates activities against defined quality criteria and calculates a maturity score. This document deliberately does **not** invent a SAMM maturity score where the responsible organizational evidence has not been evaluated against the official questions and quality criteria.

## Evidence basis

Current CORE evidence considered in this mapping includes:

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

Organizational evidence such as IAM/MFA operation, privileged-access records, management review, personnel security, supplier controls, formal training operation, and independent audit evidence is **not inferred from source code**.

## Practice-level preliminary mapping

| Business function | Security practice | Evidence status | Current evidence position | Required next evidence |
|---|---|---|---|---|
| Governance | Strategy & Metrics | PARTIAL | CORE assurance gates, evidence registers and closure tracking exist | Formal security strategy, objectives, KPIs and effectiveness review |
| Governance | Policy & Compliance | PARTIAL | ISO/IEC 27001 alignment documents and control mapping exist | Operating policy approvals, review records and organizational effectiveness evidence |
| Governance | Education & Guidance | OPEN | No sufficient objective evidence of organization-wide security education/training operation | Training plan, completed training records and security guidance ownership |
| Design | Threat Assessment | PARTIAL | Risk treatment, security boundaries and multiple security scans exist | Formal SAMM threat-assessment methodology, abuse cases and recurring review evidence |
| Design | Security Requirements | PARTIAL | Security/runtime requirements and acceptance gates exist | Requirements lifecycle, stakeholder approval and requirements-to-control traceability |
| Design | Secure Architecture | PARTIAL / GREEN TECHNICAL | CORE architecture, Money Ledger/Engine, Escrow Engine, Witness Chain, reconciliation and trust boundaries are documented | Independent architecture assessment and retained review/retest evidence |
| Implementation | Secure Build | GREEN TECHNICAL / PARTIAL MATURITY | Protected main, required CI gates, CodeQL, Scorecard work, Trivy, Snyk and OSV evidence exist | Build-policy operating evidence, approved dependency/component policy and release records |
| Implementation | Secure Deployment | PARTIAL | CI/CD governance and protected-main controls exist | Production deployment controls, rollback evidence and deployment approval records |
| Implementation | Defect Management | PARTIAL | Security findings and remediation evidence are tracked | Formal defect lifecycle, severity/SLA rules, ownership and closure/retest evidence |
| Verification | Architecture Assessment | OPEN / PENDING INDEPENDENT | Internal architecture evidence exists | Independent technical re-performance and architecture review |
| Verification | Requirements-driven Testing | GREEN TECHNICAL / PARTIAL MATURITY | CORE gates, PostgreSQL concurrency, reconciliation and transaction tests are evidenced | Complete requirements-to-test traceability and stakeholder acceptance evidence |
| Verification | Security Testing | GREEN TECHNICAL / PARTIAL MATURITY | CodeQL, Trivy, Snyk and OSV provide multiple automated security evidence sources | Manual high-risk security testing / independent penetration testing and regression evidence |
| Operations | Incident Management | OPEN | Incident-response requirements/evidence templates exist | Operating incident records, exercises, lessons learned and response metrics |
| Operations | Environment Management | PARTIAL | Container hardening/remediation and dependency scanning are active | Full environment baseline, patch cadence, monitoring and drift-control evidence |
| Operations | Operational Management | PARTIAL | Reconciliation, recovery and audit controls exist | Operational governance, management review, service metrics and corrective-action evidence |

## Evidence discipline

For each official SAMM activity question and quality criterion:

1. Evaluate the criterion against actual evidence.
2. If the criterion is not completely fulfilled, record it as **not fulfilled** rather than awarding inferred credit.
3. Distinguish technical evidence from organizational operating evidence.
4. Keep independent assessment evidence separate from self-assessment evidence.
5. Preserve the assessment against a fixed candidate baseline so later changes do not silently alter the result.

This follows the purpose of the official SAMM toolbox: review security activities against defined quality criteria and calculate the maturity score from the completed assessment. citeturn0search0

## Preliminary maturity interpretation

The current evidence supports the following **non-certifying** conclusion:

- **Technical software assurance:** substantially established for the CORE candidate.
- **Process maturity:** partially established.
- **Organizational security maturity:** insufficient evidence for a high maturity claim.
- **Independent verification:** pending.
- **OWASP SAMM formal score:** NOT CLAIMED until the official SAMM assessment questions and quality criteria are completed with responsible stakeholders.

The strongest currently evidenced areas are Secure Build, Requirements-driven Testing, Security Testing, Secure Architecture, and Environment Management.

The principal maturity gaps are Governance evidence, Education & Guidance, formal Threat Assessment process, Secure Deployment operational evidence, Defect Management lifecycle evidence, independent Architecture Assessment, Incident Management operation, and Operational Management/management review.

## Priority improvement sequence

**Priority 1 — Verification**
- Independent architecture review.
- Manual high-risk security testing.
- Requirements-to-test traceability.

**Priority 2 — Governance**
- Security objectives and metrics.
- Policy approval/review evidence.
- Education and guidance operating records.

**Priority 3 — Operations**
- Incident-response exercises and records.
- Environment baseline and patch/drift evidence.
- Management review and corrective-action evidence.

**Priority 4 — Implementation**
- Formal defect-management lifecycle.
- Production deployment and rollback evidence.
- Dependency/component approval and release records.

## International benchmark context

OWASP publishes a benchmark initiative intended to help organizations compare maturity with peers. The currently published benchmark dataset is limited, so benchmark comparisons should be treated as contextual rather than definitive. The latest published benchmark report states an average SAMM score of 1.44/3.0 across its dataset, with most data coming from large organizations and more than 80% of the dataset coming from independent third-party SAMM practitioners. citeturn1search0

GerChain should **not** compare itself numerically to this benchmark until its own official SAMM assessment is completed. A later comparison can be made by business function and practice, with scope and organization size stated explicitly.

## Next assessment step

Use the official OWASP SAMM Assessment Toolbox to answer every activity question and quality criterion with responsible stakeholders. OWASP provides both spreadsheet toolboxes and online assessment options; the Scorecard updates as the questions are completed. citeturn0search0turn0search1

The resulting SAMM score should be stored separately from this preliminary mapping and labelled **self-assessment**. It should not be represented as an independent audit or certification.

## Assurance wording

> “GerChain CORE-ийн software assurance maturity-г OWASP SAMM v2-ийн хүрээнд урьдчилан үнэлэхэд техникийн security assurance-ийн суурь бүрдсэн боловч байгууллагын процесс, үйл ажиллагаа болон хараат бус баталгаажуулалтын нотолгоо бүрэн болоогүй байна. Иймд одоогоор SAMM-ийн албан ёсны maturity score болон certification claim гаргаагүй.”

**SHUUD is excluded from this assessment.**
