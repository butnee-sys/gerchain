"""SH-16.17 schema bootstrap race audit."""

from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, inspect

from shuud.persistence import initialize_schema


def test_concurrent_schema_bootstrap_is_idempotent(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'bootstrap.db'}", future=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: _bootstrap(engine), range(4)))

    failures = [result for result in results if result is not None]
    assert failures == []
    tables = set(inspect(engine).get_table_names())
    assert "shuud_schema_version" in tables
    assert "shuud_publication_outbox" in tables


def _bootstrap(engine):
    try:
        initialize_schema(engine)
        return None
    except Exception as exc:
        return repr(exc)
