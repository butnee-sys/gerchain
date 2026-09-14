from apps.shuud.command_api import _command


def test_command_result_contains_decision_and_existing_kpi_payload():
    result = _command()
    assert result["decision"] in {"GO", "CONDITIONAL GO", "NO-GO"}
    assert "gate" in result
    assert "observed" in result
    assert "kpi" in result
    assert "one_line" in result
    assert "≤120 сек" in result["one_line"]


def test_command_does_not_invent_economic_coverage():
    result = _command()
    assert result["observed"]["economic_measurement_cases"] == result["kpi"]["economic_measurement_cases"]
    assert result["observed"]["economic_coverage_rate"] == result["kpi"]["economic_coverage_rate"]
    assert result["observed"]["total_savings_mnt"] == result["kpi"]["total_savings_mnt"]
