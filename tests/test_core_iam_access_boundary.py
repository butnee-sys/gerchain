from pathlib import Path


def test_core_iam_evidence_is_fail_closed():
    doc = Path("docs/CORE_IAM_ACCESS_EVIDENCE.md").read_text(encoding="utf-8")
    assert "GC-IDM-001" in doc
    assert "GC-IDM-002" in doc
    assert "MISSING" in doc
    assert "Source-code authorization checks are not treated as proof" in doc
    assert "PASS merely because a security mechanism exists in source code" in doc
    assert "SHUUD" in doc
