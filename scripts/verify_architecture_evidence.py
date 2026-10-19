#!/usr/bin/env python3
"""Fail-closed verifier for commit-bound EAI/PostgreSQL architecture evidence.

Input JSON contract:
{
  "repository": "owner/repo",
  "commit_sha": "<40 hex>",
  "run_id": 123,
  "run_attempt": 1,
  "artifact": {"name": "...", "sha256": "<64 hex>"},
  "checks": [{"id":"C01", "status":"PASS", "evidence":{"path":"...", "sha256":"..."}}],
  "criteria": [{"id":"AC01", "status":"PASS", "check_ids":["C01"], "evidence":[{"path":"...", "sha256":"..."}]}]
}
A PASS requires real, hashed evidence for each check and each criterion. A test/workflow success
alone is insufficient. The verifier writes a decision JSON and exits nonzero unless all gates pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

CHECK_IDS = tuple(f"C{i:02d}" for i in range(1, 14))
CRITERION_IDS = tuple(f"AC{i:02d}" for i in range(1, 18))
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def _evidence_ok(item: Any, root: Path) -> tuple[bool, str]:
    if not isinstance(item, dict):
        return False, "evidence entry is not an object"
    rel = item.get("path")
    claimed = item.get("sha256")
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        return False, "evidence path is missing or unsafe"
    if not _valid_hash(claimed):
        return False, "evidence sha256 is missing or malformed"
    path = root / rel
    if not path.is_file():
        return False, f"evidence file is missing: {rel}"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != claimed:
        return False, f"evidence hash mismatch: {rel}"
    return True, rel


def verify(document: dict[str, Any], evidence_root: Path) -> dict[str, Any]:
    issues: list[str] = []
    commit_sha = document.get("commit_sha")
    run_id = document.get("run_id")
    run_attempt = document.get("run_attempt")
    artifact = document.get("artifact")

    if not isinstance(commit_sha, str) or not COMMIT_RE.fullmatch(commit_sha):
        issues.append("commit_sha must be a full 40-character SHA")
    if not isinstance(run_id, int) or run_id <= 0:
        issues.append("run_id must be a positive integer")
    if not isinstance(run_attempt, int) or run_attempt <= 0:
        issues.append("run_attempt must be a positive integer")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("name"), str):
        issues.append("artifact name is missing")
    elif not _valid_hash(artifact.get("sha256")):
        issues.append("artifact sha256 is missing or malformed")

    checks_raw = document.get("checks")
    criteria_raw = document.get("criteria")
    checks = {x.get("id"): x for x in checks_raw if isinstance(x, dict)} if isinstance(checks_raw, list) else {}
    criteria = {x.get("id"): x for x in criteria_raw if isinstance(x, dict)} if isinstance(criteria_raw, list) else {}

    missing_checks = sorted(set(CHECK_IDS) - set(checks))
    extra_checks = sorted(set(checks) - set(CHECK_IDS))
    missing_criteria = sorted(set(CRITERION_IDS) - set(criteria))
    extra_criteria = sorted(set(criteria) - set(CRITERION_IDS))
    if missing_checks:
        issues.append("missing checks: " + ", ".join(missing_checks))
    if extra_checks:
        issues.append("unexpected check IDs: " + ", ".join(extra_checks))
    if missing_criteria:
        issues.append("missing architecture criteria: " + ", ".join(missing_criteria))
    if extra_criteria:
        issues.append("unexpected architecture criterion IDs: " + ", ".join(extra_criteria))

    check_results = []
    for check_id in CHECK_IDS:
        item = checks.get(check_id, {})
        ok, reason = _evidence_ok(item.get("evidence"), evidence_root)
        passed = item.get("status") == "PASS" and ok
        if item.get("status") != "PASS":
            reason = f"check status is {item.get('status')!r}, not PASS"
        if not passed:
            issues.append(f"{check_id}: {reason}")
        check_results.append({"id": check_id, "status": "PASS" if passed else "BLOCKED", "reason": reason})

    criterion_results = []
    for criterion_id in CRITERION_IDS:
        item = criteria.get(criterion_id, {})
        ids = item.get("check_ids")
        evidence = item.get("evidence")
        criterion_issues = []
        if item.get("status") != "PASS":
            criterion_issues.append(f"declared status is {item.get('status')!r}")
        if not isinstance(ids, list) or not ids:
            criterion_issues.append("no linked checks")
        else:
            unknown = sorted(set(ids) - set(CHECK_IDS))
            blocked = sorted(check_id for check_id in set(ids) if checks.get(check_id, {}).get("status") != "PASS")
            if unknown:
                criterion_issues.append("unknown check links: " + ", ".join(unknown))
            if blocked:
                criterion_issues.append("linked checks not PASS: " + ", ".join(blocked))
        if not isinstance(evidence, list) or not evidence:
            criterion_issues.append("no criterion-specific evidence")
        else:
            for entry in evidence:
                ok, reason = _evidence_ok(entry, evidence_root)
                if not ok:
                    criterion_issues.append(reason)
        passed = not criterion_issues
        if not passed:
            issues.append(f"{criterion_id}: " + "; ".join(criterion_issues))
        criterion_results.append({
            "id": criterion_id,
            "status": "PASS" if passed else "BLOCKED",
            "check_ids": ids if isinstance(ids, list) else [],
            "issues": criterion_issues,
        })

    passed_checks = sum(x["status"] == "PASS" for x in check_results)
    passed_criteria = sum(x["status"] == "PASS" for x in criterion_results)
    return {
        "decision": "PASS" if not issues and passed_checks == 13 and passed_criteria == 17 else "BLOCKED",
        "commit_sha": commit_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "checks": {"required": 13, "passed": passed_checks, "results": check_results},
        "architecture_criteria": {"required": 17, "passed": passed_criteria, "results": criterion_results},
        "issues": issues,
        "rule": "No PASS without exact-SHA/run-bound, file-present, SHA256-verified evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Evidence contract JSON")
    parser.add_argument("--evidence-root", default=".", help="Root directory for evidence paths")
    parser.add_argument("--output", required=True, help="Decision JSON output path")
    args = parser.parse_args()

    source = Path(args.input)
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("input root must be a JSON object")
        result = verify(document, Path(args.evidence_root).resolve())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"decision": "BLOCKED", "issues": [f"input error: {exc}"]}

    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    target.write_text(payload, encoding="utf-8")
    print(json.dumps({
        "decision": result["decision"],
        "checks_passed": result.get("checks", {}).get("passed", 0),
        "checks_required": 13,
        "criteria_passed": result.get("architecture_criteria", {}).get("passed", 0),
        "criteria_required": 17,
        "decision_json": str(target),
        "decision_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "issues": result.get("issues", []),
    }, sort_keys=True))
    return 0 if result["decision"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
