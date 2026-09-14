from pathlib import Path


def test_gate02_capability_contract_exists():
    path = Path("docs/GATE02_CAPABILITY_MATRIX.md")
    text = path.read_text(encoding="utf-8")
    for classification in (
        "AUTHORITATIVE",
        "COMPOSITE",
        "BOUNDARY",
        "POLICY",
        "STRUCTURAL",
        "MISSING",
        "DUPLICATE",
    ):
        assert classification in text


def test_gate02_blocks_missing_or_duplicate_capabilities():
    text = Path("docs/GATE02_CAPABILITY_MATRIX.md").read_text(encoding="utf-8")
    assert "`MISSING` and `DUPLICATE` block CORE freeze." in text
