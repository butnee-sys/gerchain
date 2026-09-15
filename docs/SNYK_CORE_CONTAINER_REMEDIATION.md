# GerChain CORE — Snyk Container Remediation

## Scope
GerChain CORE container/base-image security only. SHUUD is frozen and out of scope.

## Locked baseline
Original Snyk baseline from `python:3.9-slim`:

- Critical: 4
- High: 14
- Medium: 4
- Low: 130
- Total: 152
- Fixable: 92
- No supported fix: 60
- Known exploit: 0

The Snyk baseline is immutable evidence.

## Candidate remediation
The CORE container was moved to a clean Alpine 3.22 multi-stage runtime. Build-only Python packaging tools (`pip`, `setuptools`, `msgpack`) are removed from the runtime virtual environment after dependency installation. The runtime image contains only the Python runtime, required certificates/timezone/runtime libraries, the application, and the CORE virtual environment.

Candidate commit: `7f051b4dc742553198173f551196ca9d43e757fd`

## Candidate evidence
- Docker build: GREEN
- CORE Operating Reconciliation: GREEN
- PostgreSQL Concurrency: GREEN
- DEE Security Gate: GREEN
- CodeQL Advanced: GREEN
- core-gates: GREEN
- Trivy CORE image scan: GREEN
- Trivy image result: **0 Critical / 0 High / 0 Medium**
- Snyk PR check: GREEN
- Snyk project UI retest: not candidate-specific; it still points to the main branch baseline.

## Acceptance gates
1. Docker build succeeds.
2. CORE runtime starts and required runtime imports succeed.
3. CORE tests remain green.
4. PostgreSQL Concurrency remains green.
5. CORE Operating Reconciliation remains green.
6. DEE Security Gate remains green.
7. CodeQL remains green.
8. Trivy candidate scan is reviewed and has no Critical/High/Medium findings.
9. Candidate-specific Snyk verification is obtained where available.
10. Independent technical re-performance and approval are obtained.
11. Any residual findings are explicitly documented with evidence and mitigation.
12. SHUUD remains out of scope.

## Final status
Automated candidate evidence is currently GREEN, but the container remediation gate is **not finally locked** until candidate-specific external verification and the required independent review/approval are completed.

No certification or full-conformance claim is made from automated scanning alone.
