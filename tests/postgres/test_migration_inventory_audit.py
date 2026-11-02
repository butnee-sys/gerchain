from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

from scripts.audit_migration_inventory import _build_applied_history


def test_migration_inventory_fails_closed_when_live_history_is_required_but_missing(tmp_path):
    root = Path(__file__).resolve().parents[2]
    report_path = tmp_path / "migration-inventory-report.json"
    env = os.environ.copy()
    env.pop("GERCHAIN_MIGRATION_AUDIT_DATABASE_URL", None)
    env["REQUIRE_MIGRATION_HISTORY"] = "1"
    env["MIGRATION_INVENTORY_REPORT"] = str(report_path)

    result = subprocess.run(
        [sys.executable, "scripts/audit_migration_inventory.py"],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1, result.stdout + result.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "FAIL"
    assert report["applied_history"]["status"] == "REQUIRED_BUT_NOT_CONFIGURED"


def test_applied_history_reports_null_applied_at_without_crashing():
    history, valid = _build_applied_history(
        [(1, "a" * 64, None)],
        {1: "a" * 64},
        [1],
    )

    assert valid is False
    assert history["status"] == "HISTORY_MISMATCH"
    assert history["missing_applied_at_versions"] == [1]
    assert history["rows"][0]["applied_at"] is None


def test_applied_history_reports_duplicate_versions_and_checksum_mismatch():
    history, valid = _build_applied_history(
        [
            (1, "a" * 64, datetime(2026, 11, 3, tzinfo=timezone.utc)),
            (1, "b" * 64, datetime(2026, 11, 3, tzinfo=timezone.utc)),
        ],
        {1: "a" * 64},
        [1],
    )

    assert valid is False
    assert history["duplicate_versions"] == [1]
    assert history["checksum_mismatches"] == [
        {
            "version": 1,
            "applied_checksum": "b" * 64,
            "accepted_checksums": ["a" * 64],
        }
    ]


def test_applied_history_accepts_exact_versions_checksums_and_timestamps():
    applied_at = datetime(2026, 11, 3, tzinfo=timezone.utc)
    history, valid = _build_applied_history(
        [(1, "a" * 64, applied_at), (2, "b" * 64, applied_at)],
        {1: "a" * 64, 2: "b" * 64},
        [1, 2],
    )

    assert valid is True
    assert history["status"] == "CAPTURED"
    assert history["missing_applied_at_versions"] == []
    assert history["versions"] == [1, 2]
