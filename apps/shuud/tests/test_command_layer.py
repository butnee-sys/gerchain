from apps.shuud.command_layer import (
    CaseRecord,
    GateDecision,
    GateThresholds,
    build_command_summary,
    evaluate_gate,
    summarize_cases,
    validate_case,
)


def test_complete_case_is_gate_eligible_and_within_target():
    case = CaseRecord("S-001", 118.4, True, ("incident", "evidence", "shiid", "clearance", "escrow", "release", "economic"))
    result = validate_case(case)
    assert result["lifecycle_complete"] is True
    assert result["within_target"] is True
    assert result["eligible_for_gate"] is True


def test_case_validation_honors_custom_target():
    case = CaseRecord("S-001", 100, True)
    assert validate_case(case, target_seconds=90)["within_target"] is False
    assert validate_case(case, target_seconds=120)["within_target"] is True


def test_incomplete_case_is_not_gate_eligible():
    case = CaseRecord("S-002", 90, False, ("incident", "evidence", "shiid"))
    result = validate_case(case)
    assert result["lifecycle_complete"] is False
    assert result["eligible_for_gate"] is False


def test_gate_go_requires_both_operational_and_economic_targets():
    assert evaluate_gate(10, 0.96, 0.91, GateThresholds(minimum_cases=10)) == GateDecision.GO


def test_gate_conditional_when_evidence_is_not_yet_strong_enough():
    assert evaluate_gate(10, 0.85, 0.80, GateThresholds(minimum_cases=10)) == GateDecision.CONDITIONAL_GO


def test_gate_no_go_when_both_targets_are_missed():
    assert evaluate_gate(10, 0.70, 0.60, GateThresholds(minimum_cases=10)) == GateDecision.NO_GO


def test_small_sample_is_conditional_not_go():
    assert evaluate_gate(2, 1.0, 1.0) == GateDecision.CONDITIONAL_GO


def test_case_summary_is_deterministic():
    summary = summarize_cases([CaseRecord("A", 110, True), CaseRecord("B", 121, True), CaseRecord("C", None, False)])
    assert summary["total_cases"] == 3
    assert summary["measured_clearance_cases"] == 2
    assert summary["within_two_minutes_cases"] == 1
    assert summary["within_two_minutes_rate"] == 0.5
    assert summary["economic_measurement_cases"] == 2
    assert summary["economic_coverage_rate"] == 2 / 3


def test_case_summary_honors_custom_target():
    cases = [CaseRecord("A", 110, True), CaseRecord("B", 121, True)]
    assert summarize_cases(cases, target_seconds=120)["within_two_minutes_cases"] == 1
    assert summarize_cases(cases, target_seconds=130)["within_two_minutes_cases"] == 2


def test_one_line_decision_summary_is_available():
    result = build_command_summary(30, 0.967, 83.2, 77.0, 412.5, 1234567, 29, 29 / 30, GateThresholds(target_seconds=90, minimum_cases=30))
    assert result["decision"] == "GO"
    assert "30 case" in result["one_line"]
    assert "≤90 сек" in result["one_line"]
    assert "1,234,567" in result["one_line"]
