from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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
