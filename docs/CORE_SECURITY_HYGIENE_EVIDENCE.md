# GerChain CORE — Security Hygiene Evidence

## Repository baseline observations

The repository currently contains dedicated workflows for CodeQL, CORE gates, CORE reconciliation, DEE security and PostgreSQL concurrency. These are CORE assurance mechanisms.

The repository also contains application-specific workflows outside this scope. Their results must not be mixed into the CORE assurance result.

## Secret protection

The repository hygiene policy requires that credentials, private keys, certificates, local databases and runtime secrets are not committed to source control.

GitHub public-repository secret scanning is an available security control. Push protection should be enabled where repository permissions and GitHub plan/settings allow it.

## Dependency transparency

A Software Bill of Materials (SBOM) should be generated from the repository dependency graph or CI and retained as assurance evidence. SPDX is the preferred interoperable export format.

## Evidence status

- CodeQL: GREEN by existing CORE CI evidence.
- CORE gates: GREEN by existing CORE CI evidence.
- PostgreSQL concurrency: GREEN by existing CORE CI evidence.
- CORE reconciliation: GREEN by existing CORE CI evidence.
- Repository secret hygiene: PARTIAL until an actual repository secret-scan result is recorded.
- Push protection: OPEN until repository setting is independently verified.
- SBOM/dependency inventory: OPEN until a generated artifact is retained.
- Independent technical re-performance: OPEN.

## Scope exclusion

SHUUD is excluded from all status calculations in this document.
