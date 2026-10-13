from services.gerchain_runtime_factory import _constraint_definition_drift


EXPECTED = {
    "escrows_state_canonical_check": (
        "state", "created", "funded", "locked", "released", "refunded", "cancelled"
    ),
    "gerchain_ledger_balance_nonnegative": ("balance", ">=", "0"),
}


def test_schema_gate_detects_dropped_constraint_even_when_history_is_unchanged():
    drift = _constraint_definition_drift(
        EXPECTED,
        {"escrows_state_canonical_check": "CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'))"},
    )
    assert "gerchain_ledger_balance_nonnegative" in drift
    assert drift["gerchain_ledger_balance_nonnegative"]["actual"] is None


def test_schema_gate_detects_constraint_recreated_on_wrong_column():
    drift = _constraint_definition_drift(
        EXPECTED,
        {
            "escrows_state_canonical_check": "CHECK (state IN ('CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'))",
            "gerchain_ledger_balance_nonnegative": "CHECK (version >= 0)",
        },
    )
    assert drift["gerchain_ledger_balance_nonnegative"]["missing_fragments"] == ["balance"]


def test_schema_gate_detects_weakened_constraint_definition():
    drift = _constraint_definition_drift(
        EXPECTED,
        {
            "escrows_state_canonical_check": "CHECK (state IS NOT NULL)",
            "gerchain_ledger_balance_nonnegative": "CHECK (balance > -100)",
        },
    )
    assert "escrows_state_canonical_check" in drift
    assert "created" in drift["escrows_state_canonical_check"]["missing_fragments"]
    assert ">=" in drift["gerchain_ledger_balance_nonnegative"]["missing_fragments"]


def test_schema_gate_accepts_expected_constraint_semantics_with_postgres_parentheses():
    drift = _constraint_definition_drift(
        EXPECTED,
        {
            "escrows_state_canonical_check": "CHECK (((state)::text = ANY ((ARRAY['CREATED'::character varying, 'FUNDED'::character varying, 'LOCKED'::character varying, 'RELEASED'::character varying, 'REFUNDED'::character varying, 'CANCELLED'::character varying])::text[])))",
            "gerchain_ledger_balance_nonnegative": "CHECK ((balance >= 0))",
        },
    )
    assert drift == {}
