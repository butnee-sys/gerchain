# GerChain CORE — International Free Assurance Pre-Assessment

**Assessment branch:** `assurance/osv-core-candidate`  
**Technical candidate under review:** `7f051b4dc742553198173f551196ca9d43e757fd`  
**Scope:** GerChain CORE only  
**SHUUD:** OUT OF SCOPE

## 1. Automated technical evidence

| Source | Scope | Current result | Status |
|---|---|---:|---|
| OpenSSF Scorecard | repository / supply-chain posture | workflow configured; independent approval pending on PR #71 | 🟡 |
| OSV-Scanner | CORE runtime dependency file | 0 findings; workflow `34971480777` successful | 🟢 |
| Trivy | CORE container | 0 Critical / 0 High / 0 Medium | 🟢 |
| Snyk PR check | candidate branch security check | SUCCESS | 🟢 |
| Snyk project | historical `main` Dockerfile baseline | 4C / 14H / 4M / 130L | 🔴 baseline only |
| CodeQL | static analysis | CORE gate green | 🟢 |

## 2. OSV-Scanner evidence

The OSV assessment was run from a branch created from the CORE candidate. The scan was deliberately restricted to:

`requirements-dee-security.txt`

The file currently contains only the intended CORE runtime dependencies:

- `cryptography>=48,<51`
- `sqlalchemy>=2,<3`
- `psycopg[binary]>=3.2,<4`

The OSV-Scanner workflow completed successfully and produced a SARIF artifact. The SARIF result contains zero vulnerability results.

This is **automated international dependency evidence**, not an independent human audit or certification.

## 3. OWASP SAMM — preliminary readiness

OWASP SAMM is appropriate for a maturity assessment of the software-security lifecycle. A numeric SAMM score is intentionally **not claimed yet**, because a valid assessment requires organizational/process evidence in addition to repository evidence.

Evidence already available for a future SAMM assessment includes:

- secure build / CI gates;
- CodeQL SAST;
- dependency and container scanning;
- security policy and disclosure process;
- branch protection and review controls;
- transaction/concurrency testing;
- reconciliation and recovery controls;
- audit/evidence documentation;
- cryptographic controls.

Remaining evidence requiring organizational confirmation includes IAM/MFA operation, privileged access, incident management, supplier controls, personnel controls, management review, internal audit, and independent assessment.

## 4. CSA STAR Level 1 — preliminary readiness

CSA STAR Level 1 is a cloud-security self-assessment based on CAIQ/CCM. It is suitable if GerChain CORE is presented as a cloud/digital infrastructure service.

No STAR Level 1 claim is made by this document. A future CAIQ assessment should be performed against the actual service boundary, responsibility model, operating environment, and organizational controls.

## 5. Independent review

Independent technical re-performance remains OPEN under GitHub Issue #74.

Required final independent record:

1. reviewer / reviewing organization;
2. exact commit SHA reviewed;
3. scope and methodology;
4. findings and severity;
5. remediation and retest status;
6. residual limitations.

No merge of PR #75 is authorized until independent re-performance and required independent approval are satisfied.

## 6. Assurance conclusion

The current evidence supports the following wording only:

> GerChain CORE has undergone multiple free automated international security checks, including OpenSSF Scorecard, OSV-Scanner, Trivy, Snyk and CodeQL. The current candidate has green automated technical evidence in the verified scopes, while independent technical re-performance and organizational assurance evidence remain outstanding.

This document does **not** constitute ISO/IEC 27001 certification, SOC 2 attestation, CSA STAR Level 2 certification, or an independent security audit.
