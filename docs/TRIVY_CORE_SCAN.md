# Trivy CORE Security Scan

## Scope

This scan covers **GerChain CORE only**. SHUUD is frozen and explicitly out of scope.

## Purpose

Trivy provides a second independent automated technical signal alongside the locked Snyk container baseline. It scans:

1. the built CORE Docker image for vulnerabilities, secrets, and misconfiguration;
2. the repository filesystem for vulnerabilities, secrets, and misconfiguration.

## Baseline

Snyk baseline recorded before remediation:

- Critical: 4
- High: 14
- Medium: 4
- Low: 130
- Total: 152

The Snyk baseline remains immutable evidence. Trivy results are a separate evidence source and must not be substituted for the original Snyk result.

## Acceptance rule

This gate is GREEN only when the Trivy workflow completes successfully and the resulting findings are reviewed. A successful workflow alone does not mean that all vulnerabilities are absent; findings must be compared against the Snyk baseline and remediation status.

No certification or full-conformance claim is made from this scan.
