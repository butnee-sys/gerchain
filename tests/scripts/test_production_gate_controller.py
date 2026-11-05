from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import sys

from postgres.migrations import _canonical_migration_files
from scripts.production_gate_controller import REQUIRED_GATES, decide, resolve_artifact_evidence


def _manifest(sha: str) -> dict:
    migration_dir = Path("postgres/migrations")
    canonical_paths = _canonical_migration_files(migration_dir)
    migrations = []
    rows = []
    for version, path in enumerate(canonical_paths, start=1):
        raw = path.read_bytes()
        sql = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        migrations.append({
            "version": version,
            "path": path.as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "runner_checksum": checksum,
            "database_checksum": checksum,
            "database_checksum_matches_runner": True,
        })
        rows.append({
            "version": version,
            "checksum": checksum,
            "applied_at": "2026-10-19T00:00:00+00:00",
        })
    return {
        "commit_sha": sha,
        "checked_out_head_sha": sha,
        "commit_sha_matches_head": True,
        "canonical_migration_count": len(canonical_paths),
        "canonical_migrations": migrations,
        "schema_version_rows": rows,
        "database_manifest_error": None,
    }


def _outcomes() -> dict[str, str]:
    return {gate: "success" for gate in REQUIRED_GATES}


def _write_manifest(tmp_path: Path, value: dict) -> Path:
    value.setdefault("lock_policy", {
        "all_30_gates_must_pass": True,
        "same_exact_commit_sha_required": True,
        "workflow_run_and_attempt_required": True,
        "missing_or_stale_evidence_means_pass": False,
        "external_organizational_evidence_required": True,
        "production_lock_authorized": True,
    })
    if "external_organizational_evidence" not in value:
        evidence_root = tmp_path / "external-organizational-evidence"
        evidence_root.mkdir(parents=True, exist_ok=True)
        domains = (
            "iam_mfa_privileged_access",
            "observability_alerting_slo",
            "performance_stress_capacity",
            "backup_restore_rpo_rto",
            "incident_recovery",
            "ci_release_governance",
            "independent_human_review",
            "authorized_release_approval",
        )
        records = []
        for domain in domains:
            relative_path = Path("external-organizational-evidence") / f"{domain}.txt"
            evidence_file = tmp_path / relative_path
            evidence_file.write_text(f"test-only evidence for {domain}", encoding="utf-8")
            records.append({
                "domain": domain,
                "commit_sha": value.get("commit_sha"),
                "path": relative_path.as_posix(),
                "sha256": hashlib.sha256(evidence_file.read_bytes()).hexdigest(),
            })
        value["external_organizational_evidence"] = {
            "status": "VERIFIED",
            "commit_sha": value.get("commit_sha"),
            "verified_by": "test-independent-reviewer",
            "verified_at": "2026-11-05T00:00:00+00:00",
            "authorized_by": "test-authorized-approver",
            "authorized_at": "2026-11-05T00:01:00+00:00",
            "evidence": records,
        }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path



def test_artifact_evidence_accepts_only_confined_local_files(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifact"
    (artifact_root / "logs").mkdir(parents=True)
    evidence = artifact_root / "logs" / "proof.txt"
    evidence.write_text("verified evidence", encoding="utf-8")

    assert resolve_artifact_evidence(artifact_root, "logs/proof.txt") == evidence.resolve()
    assert resolve_artifact_evidence(artifact_root, "https://github.com/acme/repo/blob/abc123/proof.txt") is None
    assert resolve_artifact_evidence(artifact_root, "urn:evidence:abc123:proof") is None
    assert resolve_artifact_evidence(artifact_root, "../outside.txt") is None
    assert resolve_artifact_evidence(artifact_root, str(evidence.resolve())) is None
    assert resolve_artifact_evidence(artifact_root, "logs/missing.txt") is None


def test_artifact_evidence_rejects_symlink_escape(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifact"
    artifact_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (artifact_root / "escape.txt").symlink_to(outside)

    assert resolve_artifact_evidence(artifact_root, "escape.txt") is None


def test_controller_locks_only_when_every_gate_and_migration_evidence_match(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, _manifest("abc123"))
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "LOCKED"
    assert report["failures"] == []
    assert report["passed_gate_count"] == 30


def test_controller_fails_closed_when_any_gate_is_missing_or_skipped(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, _manifest("abc123"))
    outcomes = _outcomes()
    outcomes["production_boot"] = "skipped"
    del outcomes["deep_reconciliation"]
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", outcomes)
    assert report["decision"] == "NOT_LOCKED"
    assert "GATE_PRODUCTION_BOOT_NOT_SUCCESS" in report["failures"]
    assert "GATE_DEEP_RECONCILIATION_MISSING" in report["failures"]


def test_controller_fails_closed_on_stale_sha_and_database_checksum_mismatch(tmp_path: Path) -> None:
    data = _manifest("oldsha")
    data["schema_version_rows"][4]["checksum"] = "tampered"
    manifest = _write_manifest(tmp_path, data)
    with patch("scripts.production_gate_controller._head_sha", return_value="newsha"):
        report = decide(manifest, "newsha", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "MANIFEST_SHA_MISMATCH" in report["failures"]
    assert "MIGRATION_DATABASE_CHECKSUM_MISMATCH_VERSION_5" in report["failures"]


def test_controller_fails_closed_when_migration_file_hash_is_tampered(tmp_path: Path) -> None:
    data = _manifest("abc123")
    data["canonical_migrations"][0]["sha256"] = "tampered"
    manifest = _write_manifest(tmp_path, data)
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "MIGRATION_FILE_SHA256_MISMATCH_VERSION_1" in report["failures"]


def test_controller_fails_closed_when_applied_at_is_missing(tmp_path: Path) -> None:
    data = _manifest("abc123")
    data["schema_version_rows"][0]["applied_at"] = None
    manifest = _write_manifest(tmp_path, data)
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "MIGRATION_APPLIED_AT_MISSING_VERSION_1" in report["failures"]


def test_controller_fails_closed_when_schema_version_rows_are_incomplete(tmp_path: Path) -> None:
    data = _manifest("abc123")
    data["schema_version_rows"].pop()
    manifest = _write_manifest(tmp_path, data)
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "SCHEMA_VERSION_ROWS_NOT_CONTIGUOUS" in report["failures"]


def test_controller_fails_closed_when_manifest_is_missing(tmp_path: Path) -> None:
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(tmp_path / "missing.json", "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert any(item.startswith("MANIFEST_UNREADABLE_") for item in report["failures"])


def test_controller_cli_accepts_expected_sha_alias() -> None:
    from scripts.production_gate_controller import _parse_args

    with patch.object(sys, "argv", [
        "production_gate_controller.py",
        "--expected-sha",
        "candidate-sha",
    ]):
        args = _parse_args()
    assert args.expected_source_sha == "candidate-sha"



def test_controller_fails_closed_when_source_policy_withholds_production_authorization(tmp_path: Path) -> None:
    data = _manifest("abc123")
    data["lock_policy"] = {
        "all_30_gates_must_pass": True,
        "same_exact_commit_sha_required": True,
        "workflow_run_and_attempt_required": True,
        "missing_or_stale_evidence_means_pass": False,
        "external_organizational_evidence_required": True,
        "production_lock_authorized": False,
    }
    manifest = _write_manifest(tmp_path, data)
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "LOCK_POLICY_PRODUCTION_LOCK_AUTHORIZED_NOT_SATISFIED" in report["failures"]


def test_controller_fails_closed_when_external_organizational_evidence_is_missing(tmp_path: Path) -> None:
    data = _manifest("abc123")
    data["external_organizational_evidence"] = None
    manifest = _write_manifest(tmp_path, data)
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "EXTERNAL_ORGANIZATIONAL_EVIDENCE_MISSING" in report["failures"]


def test_controller_fails_closed_on_external_evidence_sha_and_file_hash_mismatch(tmp_path: Path) -> None:
    data = _manifest("abc123")
    evidence_root = tmp_path / "external-organizational-evidence"
    evidence_root.mkdir(parents=True)
    item_path = evidence_root / "iam-proof.txt"
    item_path.write_text("tampered after reviewer verification", encoding="utf-8")
    data["external_organizational_evidence"] = {
        "status": "VERIFIED",
        "commit_sha": "stale-sha",
        "verified_by": "test-independent-reviewer",
        "verified_at": "2026-11-05T00:00:00+00:00",
        "authorized_by": "test-authorized-approver",
        "authorized_at": "2026-11-05T00:01:00+00:00",
        "evidence": [{
            "domain": "iam_mfa_privileged_access",
            "commit_sha": "stale-sha",
            "path": "external-organizational-evidence/iam-proof.txt",
            "sha256": "0" * 64,
        }],
    }
    manifest = _write_manifest(tmp_path, data)
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "EXTERNAL_ORGANIZATIONAL_EVIDENCE_SHA_MISMATCH" in report["failures"]
    assert "EXTERNAL_ORGANIZATIONAL_EVIDENCE_HASH_MISMATCH_IAM_MFA_PRIVILEGED_ACCESS" in report["failures"]
    assert "EXTERNAL_ORGANIZATIONAL_EVIDENCE_DOMAIN_MISSING_AUTHORIZED_RELEASE_APPROVAL" in report["failures"]


def test_controller_fails_closed_when_external_evidence_path_escapes_artifact(tmp_path: Path) -> None:
    data = _manifest("abc123")
    _write_manifest(tmp_path, data)  # materialize the synthetic, hash-bound test evidence first
    data["external_organizational_evidence"]["evidence"][0]["path"] = "../outside.txt"
    manifest = _write_manifest(tmp_path, data)
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "EXTERNAL_ORGANIZATIONAL_EVIDENCE_FILE_MISSING_OR_UNSAFE_IAM_MFA_PRIVILEGED_ACCESS" in report["failures"]
