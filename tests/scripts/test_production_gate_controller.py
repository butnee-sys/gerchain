from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from postgres.migrations import _canonical_migration_files, checksum
from scripts.production_gate_controller import REQUIRED_GATES, decide


def _manifest(sha: str) -> dict:
    migrations = []
    rows = []
    for path in _canonical_migration_files(Path("postgres/migrations")):
        version = int(path.name.split("_", 1)[0])
        runner_checksum = checksum(path.read_text(encoding="utf-8"))
        migrations.append({
            "version": version,
            "path": path.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "runner_checksum": runner_checksum,
            "database_checksum": runner_checksum,
            "database_checksum_matches_runner": True,
            "bytes": path.stat().st_size,
        })
        rows.append({
            "version": version,
            "checksum": runner_checksum,
            "applied_at": "2026-10-19T00:00:00+00:00",
        })
    return {
        "commit_sha": sha,
        "checked_out_head_sha": sha,
        "commit_sha_matches_head": True,
        "canonical_migration_count": 17,
        "canonical_migrations": migrations,
        "schema_version_rows": rows,
        "database_manifest_error": None,
    }


def _outcomes() -> dict[str, str]:
    return {gate: "success" for gate in REQUIRED_GATES}


def test_controller_locks_only_when_every_gate_and_manifest_match(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_manifest("abc123")), encoding="utf-8")
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "LOCKED"
    assert report["failures"] == []


def test_controller_fails_closed_when_any_gate_is_missing_or_skipped(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_manifest("abc123")), encoding="utf-8")
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
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    with patch("scripts.production_gate_controller._head_sha", return_value="newsha"):
        report = decide(manifest, "newsha", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "MANIFEST_SHA_MISMATCH" in report["failures"]
    assert "MIGRATION_CHECKSUM_MISMATCH_VERSION_5" in report["failures"]


def test_controller_fails_closed_when_migration_file_hash_is_tampered(tmp_path: Path) -> None:
    manifest_data = _manifest("abc123")
    manifest_data["canonical_migrations"][0]["sha256"] = "0" * 64
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(manifest, "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert "MIGRATION_FILE_SHA256_MISMATCH_VERSION_1" in report["failures"]


def test_controller_fails_closed_when_manifest_is_missing(tmp_path: Path) -> None:
    with patch("scripts.production_gate_controller._head_sha", return_value="abc123"):
        report = decide(tmp_path / "missing.json", "abc123", _outcomes())
    assert report["decision"] == "NOT_LOCKED"
    assert any(item.startswith("MANIFEST_UNREADABLE_") for item in report["failures"])
