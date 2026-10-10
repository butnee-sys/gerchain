from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


class _NoopFactory(ProductionRuntimeFactory):
    def initialize(self) -> None:
        # Real schema creation is covered only by a PostgreSQL integration gate.
        pass


def test_factory_create_configures_canonical_ledger_authority() -> None:
    engine = Mock()
    engine.dialect.name = "postgresql"
    connection = Mock()
    connect_context = MagicMock()
    connect_context.__enter__.return_value = connection
    connect_context.__exit__.return_value = None
    engine.connect.return_value = connect_context

    factory = _NoopFactory(
        ProductionRuntimeConfig(
            database_url="postgresql+psycopg://test/test",
            escrow_id="esc-1",
            amount=100,
            currency="MNT",
            witness_id="wit-1",
        ),
        engine=engine,
    )

    with (
        patch("services.gerchain_runtime_factory.assert_canonical_production_schema") as schema_check,
        patch.object(factory, "_validate_configured_escrow") as escrow_check,
    ):
        runtime = factory.create()

    schema_check.assert_called_once_with(connection)
    escrow_check.assert_called_once_with()
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"


def test_factory_rejects_non_postgresql_engine() -> None:
    engine = Mock()
    engine.dialect.name = "sqlite"

    try:
        _NoopFactory(
            ProductionRuntimeConfig(
                database_url="postgresql+psycopg://test/test",
                escrow_id="esc-1",
                amount=100,
                currency="MNT",
                witness_id="wit-1",
            ),
            engine=engine,
        )
    except ValueError as exc:
        assert str(exc) == "ProductionRuntimeFactory requires a PostgreSQL engine"
    else:
        raise AssertionError("non-PostgreSQL engine must be rejected")


def test_factory_initialize_uses_canonical_migration_runner() -> None:
    engine = Mock()
    engine.dialect.name = "postgresql"
    connection = Mock()
    connect_context = MagicMock()
    connect_context.__enter__.return_value = connection
    connect_context.__exit__.return_value = None
    engine.connect.return_value = connect_context

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url="postgresql+psycopg://test/test",
            escrow_id="esc-1",
            amount=100,
            currency="MNT",
            witness_id="wit-1",
        ),
        engine=engine,
    )

    with patch("services.gerchain_runtime_factory.initialize_canonical_postgres_schema") as initializer:
        factory.initialize()

    initializer.assert_called_once_with(engine)



def _factory_for_escrow_validation():
    from contextlib import contextmanager
    from types import SimpleNamespace

    engine = Mock()
    engine.dialect.name = "postgresql"
    factory = _NoopFactory(
        ProductionRuntimeConfig(
            database_url="postgresql+psycopg://test/test",
            escrow_id="esc-1",
            amount=100,
            currency="MNT",
            witness_id="wit-1",
        ),
        engine=engine,
    )
    return factory, SimpleNamespace


def test_configured_escrow_validation_accepts_matching_canonical_record() -> None:
    factory, namespace = _factory_for_escrow_validation()
    escrow = namespace(
        id="esc-1",
        amount=100,
        currency="MNT",
        sender_address="SRC",
        receiver_address="BEN",
        refund_destination="SRC",
    )
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = escrow
    context = MagicMock()
    context.__enter__.return_value = session
    context.__exit__.return_value = None
    factory.session_factory = Mock(return_value=context)

    factory._validate_configured_escrow()


def test_configured_escrow_validation_rejects_missing_canonical_record() -> None:
    factory, _ = _factory_for_escrow_validation()
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None
    context = MagicMock()
    context.__enter__.return_value = session
    context.__exit__.return_value = None
    factory.session_factory = Mock(return_value=context)

    import pytest
    with pytest.raises(RuntimeError, match="absent from canonical PostgreSQL state"):
        factory._validate_configured_escrow()


def test_configured_escrow_validation_rejects_amount_currency_and_party_mismatch() -> None:
    import pytest

    for field, value, message in (
        ("amount", 101, "amount does not match"),
        ("currency", "USD", "currency does not match"),
        ("refund_destination", None, "missing authoritative party/refund fields"),
    ):
        factory, namespace = _factory_for_escrow_validation()
        escrow = namespace(
            id="esc-1",
            amount=100,
            currency="MNT",
            sender_address="SRC",
            receiver_address="BEN",
            refund_destination="SRC",
        )
        setattr(escrow, field, value)
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = escrow
        context = MagicMock()
        context.__enter__.return_value = session
        context.__exit__.return_value = None
        factory.session_factory = Mock(return_value=context)

        with pytest.raises(RuntimeError, match=message):
            factory._validate_configured_escrow()
