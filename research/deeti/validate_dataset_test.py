from pathlib import Path

from validate_dataset import DATA, validate


def test_schema_only_dataset_is_valid(capsys):
    assert DATA.exists()
    assert validate() == 0
    output = capsys.readouterr().out
    assert "schema-only" in output


def test_validator_recomputes_eti_formula(tmp_path):
    original = DATA.read_text(encoding="utf-8")
    try:
        DATA.write_text(
            "observation_id,domain,jurisdiction,period,et_trust,et_transparency,et_fulfilment,eti,transaction_value,transaction_complexity,verification_time,completion_time,settlement_delay,failure_flag,dispute_flag,evidence_complete,condition_verified,correct_settlement,direct_cost,control_group,data_source,source_version\n"
            "x,domain,jurisdiction,2026,0.9,0.8,0.7,0.0,1,1,1,1,1,0,0,1,1,1,1,1,source,v1\n",
            encoding="utf-8",
        )
        try:
            validate()
        except ValueError as exc:
            assert "eti does not equal" in str(exc)
        else:
            raise AssertionError("invalid ETI should be rejected")
    finally:
        DATA.write_text(original, encoding="utf-8")
