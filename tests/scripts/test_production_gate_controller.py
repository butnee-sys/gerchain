from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scripts.production_gate_controller import REQUIRED_GATES, decide


def _manifest(sha: str) -> dict:
    migrations = []
    rows = []
    for version in range(1, 18):
        checksum = f"checksum-{version}"
        migrations.append({"version": version, "runner_checksum": checksum})
        rows.append(
            {
                "version": version,
                "checksum": checksum,
                "applied_at": "2026-10-19T00:00:00+00:00",
            }
        )
    return {
        "commit_sha": sha,
        "source_commit_sha": sha,
        "checked_out_head_sha": sha,
        "commit_sha_matches_head": True,
        "canonical_migration_count": 17,
        "canonical_migrations": migrations,
        "schema_version_rows": rows,
        "database_manifest_error": None,
    }


def _outcomes() -> dict[str, str]:
    return {gate: "success" for gate in REQUIRED_GATES}


def _write_manifest(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_controller_locks_only_when_every_gate_and_manifest_match(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "manifest.json", _manifest("abc123"))
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "LOCKED"
    assert report["failures"] == []


def test_controller_fails_closed_when_any_gate_is_missing_or_skipped(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "manifest.json", _manifest("abc123"))
    outcomes = _outcomes()
    outcomes["production_boot"] = "skipped"
    del outcomes["deep_reconciliation"]
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", outcomes)
    assert report["decision"] == "NOT_LOCKED"
    assert "GATE_PRODUCTION_BOOT_SKIPPED" in report["failures"]
    assert "GATE_DEEP_RECONCILIATION_MISSING" in report["failures"]


def test_controller_fails_closed_on_stale_sha_and_checksum_mismatch(tmp_path: Path) -> None:
    manifest_data = _manifest("oldsha")
    manifest_data["schema_version_rows"][4]["checksum"] = "tampered"
    manifest = _write_manifest(tmp_path / "manifest.json", manifest_data)
    with patch("scripts.production_gate_controller._head_sha", return_value="newsha"):
        report = decide(manifest, "newsha", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "MANIFEST_SHA_MISMATCH" in report["failures"]
    assert "MANIFEST_HEAD_SHA_MISMATCH" in report["failures"]
    assert "MIGRATION_CHECKSUM_MISMATCH_VERSION_5" in report["failures"]


def test_controller_fails_closed_when_manifest_is_missing(tmp_path: Path) -> None:
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(tmp_path / "missing.json", "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "MANIFEST_NOT_FOUND" in report["failures"]


def test_controller_fails_closed_when_migration_history_is_empty(tmp_path: Path) -> None:
    data = _manifest("abc123")
    data["schema_version_rows"] = []
    data["canonical_migration_count"] = 0
    manifest = _write_manifest(tmp_path / "manifest.json", data)
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "MIGRATION_HISTORY_MISSING" in report["failures"]


def test_controller_rejects_unknown_gates_and_missing_expected_sha(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "manifest.json", _manifest("abc123"))
    outcomes = _outcomes()
    outcomes["surprise_gate"] = "success"
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "", outcomes)
    assert report["decision"] == "NOT_LOCKED"
    assert "EXPECTED_SHA_MISSING" in report["failures"]
    assert "GATE_UNKNOWN_SURPRISE_GATE" in report["failures"]


def test_controller_rejects_manifest_head_flag_not_confirmed(tmp_path: Path) -> None:
    data = _manifest("abc123")
    data["commit_sha_matches_head"] = False
    manifest = _write_manifest(tmp_path / "manifest.json", data)
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "MANIFEST_COMMIT_HEAD_MATCH_NOT_CONFIRMED" in report["failures"]
