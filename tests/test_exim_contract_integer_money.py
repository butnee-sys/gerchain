"""Contract-level tests for the EXIM Escrow Port boundary."""

from __future__ import annotations

import pytest

from nef_gerchain_port import (
    ContractRequest,
    EscrowRequest,
    ExportedSettlement,
    ExternalPortImport,
    PaymentRequest,
    require_integer_money,
)


def test_canonical_contract_alias_is_public() -> None:
    assert ContractRequest.__name__ == "ContractImportRequest"


def test_money_helper_rejects_float_and_bool() -> None:
    with pytest.raises(TypeError, match="integer amount"):
        require_integer_money(1000.5)
    with pytest.raises(TypeError, match="integer amount"):
        require_integer_money(True)
    assert require_integer_money(1000) == 1000


def test_money_dataclasses_reject_non_integer_amounts() -> None:
    with pytest.raises(TypeError, match="escrow amount"):
        EscrowRequest(escrow_id="E-1", amount=1000.5)
    with pytest.raises(TypeError, match="payment amount"):
        PaymentRequest(escrow_id="E-1", amount=1000.5)
    with pytest.raises(TypeError, match="settlement amount"):
        ExportedSettlement(
            port_version="1.0",
            escrow_id="E-1",
            status="SETTLED",
            amount=1000.5,
            currency="MNT",
            settlement_provider="NEF",
        )


def test_port_nef_state_engine_accepts_only_integer_units() -> None:
    port = ExternalPortImport()
    engine = port.nef_state_engine(static_pool=2_000_000, dynamic_limit=2_000_000)
    assert engine.get_static_pool() == 2_000_000
    assert engine.get_dynamic_limit() == 2_000_000

    with pytest.raises(TypeError, match="static pool"):
        port.nef_state_engine(static_pool=2_000_000.5, dynamic_limit=2_000_000)


def test_port_payment_validates_positive_integer() -> None:
    port = ExternalPortImport()
    assert port.create_payment(PaymentRequest(escrow_id="E-1", amount=2_000_000)).amount == 2_000_000
    with pytest.raises(ValueError, match="positive integer"):
        port.create_payment(PaymentRequest(escrow_id="E-1", amount=0))
