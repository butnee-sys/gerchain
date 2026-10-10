from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
    initialize_canonical_postgres_schema,
)


class _NoopFactory(ProductionRuntimeFactory):
    def initialize(self) -> None:
        pass


def _config() -> ProductionRuntimeConfig:
    return ProductionRuntimeConfig(
        database_url="postgresql+psycopg://test/test",
        escrow_id="esc-1",
        amount=100,
        currency="MNT",
        witness_id="wit-1",
    )


def _postgres_engine():
    engine = Mock()
    engine.dialect.name = "postgresql"
    engine.url = "postgresql+psycopg://test/test"
    return engine


def test_factory_create_configures_canonical_ledger_authority() -> None:
    engine = _postgres_engine()
    factory = _NoopFactory(_config(), engine=engine)

    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"
    assert runtime._session_factory is not None
    assert runtime._canonical_ledger is not None


def test_factory_rejects_non_postgresql_engine() -> None:
    engine = _postgres_engine()
    engine.dialect.name = "sqlite"
    with pytest.raises(ValueError, match="requires a PostgreSQL engine"):
        _NoopFactory(_config(), engine=engine)


def test_factory_initialize_uses_canonical_migration_runner() -> None:
    engine = _postgres_engine()
    factory = ProductionRuntimeFactory(_config(), engine=engine)
    with patch("services.gerchain_runtime_factory.initialize_canonical_postgres_schema") as initializer:
        factory.initialize()
    initializer.assert_called_once_with(engine)


def test_schema_initializer_rejects_non_postgresql_engine() -> None:
    engine = _postgres_engine()
    engine.dialect.name = "sqlite"
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        initialize_canonical_postgres_schema(engine)


def test_factory_rejects_non_postgresql_url() -> None:
    engine = _postgres_engine()
    config = ProductionRuntimeConfig(
        database_url="sqlite:///test.db",
        escrow_id="esc-1",
        amount=100,
        currency="MNT",
        witness_id="wit-1",
    )
    with pytest.raises(ValueError, match="requires a PostgreSQL database URL"):
        _NoopFactory(config, engine=engine)
