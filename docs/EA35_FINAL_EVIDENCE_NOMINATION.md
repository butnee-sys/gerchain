# EA-35 Final Evidence Nomination

Status: IN PROGRESS / NOT LOCKED
Scope: Fundamental architecture + EAI only. Product layers excluded.

## Candidate policy
The commit that adds this evidence record is the exact-SHA candidate for fresh branch CI. No prior commit is declared production-ready solely from historical checks.

## Evidence observed before this candidate
- Commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` corrected the production entrypoint to construct `ProductionRuntimeFactory` as an instance.
- Historical GitHub Actions run `36542458201` (PostgreSQL Concurrency) failed: `test_migrations_are_serialized_and_checksum_is_stable` reported duplicate `schema_version(version=2)`.
- Historical GitHub Actions run `36542458205` (core-gates) failed during collection because `services/gerchain_runtime.py` contained literal escaped newline text in a method definition. This is historical evidence and must not be confused with the current branch file, which was inspected separately.
- The current branch migration runner uses a session-scoped PostgreSQL advisory lock, a schema_version table lock, duplicate-history checks/repair for identical rows, a unique version index, and conflict-safe publication. These source-level protections are not a substitute for a fresh successful PostgreSQL run.

## Required exact-SHA evidence
1. Workflow YAML validation.
2. Python compile check.
3. Canonical architecture/boundary tests.
4. PostgreSQL migration concurrency test on a dedicated fresh database, with two distinct backend PIDs and exactly one checksum row per migration version.
5. PostgreSQL canonical runtime factory and production entrypoint integration tests.
6. Deep value-truth reconciliation tests against PostgreSQL.
7. Full applicable CI and security checks for this exact SHA.
8. Independent re-performance and explicit final lock decision.

## Lock rule
Any failed, missing, stale, or ambiguous check blocks FINAL LOCK. Do not infer success from source inspection, a green unrelated status, or a previous SHA.
