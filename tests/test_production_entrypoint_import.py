from __future__ import annotations


def test_production_entrypoint_imports_cleanly() -> None:
    import production_entrypoint

    assert production_entrypoint.main is not None
