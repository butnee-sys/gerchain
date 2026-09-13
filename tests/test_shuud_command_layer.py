from shuud.command_layer import (
    CaseRecord,
    GateDecision,
    GateThresholds,
    build_command_summary,
    evaluate_gate,
    summarize_cases,
    validate_case,
)


def test_complete_case_is_gate_eligible_and_within_target():
    case = CaseRecord(
        case_id="S-001",
        clearance_seconds=118.4,
        economic_measured=True,
        lifecycle=("incident", "evidence", "shiid", "clearance", "escrow", "release", "economic"),
    )
    result = validate_case(case)
    assert result["lifecycle_complete"] is True
    assert result["within_target"] is True
    assert result["eligible_for_gate"] is True


def test_case_validation_honors_custom_target():
    case = CaseRecord("S-001", 100, True)
    assert validate_case(case, target_seconds=90)["within_target"] is False
    assert validate_case(case, target_seconds=120)["within_target"] is True


def test_incomplete_case_is_not_gate_eligible():
    case = CaseRecord(
        case_id="S-002",
        clearance_seconds=90,
        economic_measured=False,
        lifecycle=("incident", "evidence", "shiid"),
    )
    result = validate_case(case)
    assert result["lifecycle_complete"] is False
    assert result["eligible_for_gate"] is False


def test_gate_go_requires_both_operational_and_economic_targets():
    thresholds = GateThresholds(minimum_cases=10)
    assert (
        evaluate_gate(
            total_cases=10,
            within_two_minutes_rate=0.96,
            economic_coverage_rate=0.91,
            thresholds=thresholds,
        )
        == GateDecision.GO
    )


def test_gate_conditional_when_evidence_is_not_yet_strong_enough():
    thresholds = GateThresholds(minimum_cases=10)
    assert (
        evaluate_gate(
            total_cases=10,
            within_two_minutes_rate=0.85,
            economic_coverage_rate=0.80,
            thresholds=thresholds,
        )
        == GateDecision.CONDITIONAL_GO
    )


def test_gate_no_go_when_both_targets_are_missed():
    thresholds = GateThresholds(minimum_cases=10)
    assert (
        evaluate_gate(
            total_cases=10,
            within_two_minutes_rate=0.70,
            economic_coverage_rate=0.60,
            thresholds=thresholds,
        )
        == GateDecision.NO_GO
    )


def test_small_sample_is_conditional_not_go():
    assert (
        evaluate_gate(
            total_cases=2,
            within_two_minutes_rate=1.0,
            economic_coverage_rate=1.0,
        )
        == GateDecision.CONDITIONAL_GO
    )


def test_case_summary_is_deterministic():
    cases = [
        CaseRecord("A", 110, True),
        CaseRecord("B", 121, True),
        CaseRecord("C", None, False),
    ]
    summary = summarize_cases(cases)
    assert summary["total_cases"] == 3
    assert summary["measured_clearance_cases"] == 2
    assert summary["within_two_minutes_cases"] == 1
    assert summary["within_two_minutes_rate"] == 0.5
    assert summary["economic_measurement_cases"] == 2
    assert summary["economic_coverage_rate"] == 2 / 3


def test_case_summary_honors_custom_target():
    cases = [CaseRecord("A", 110, True), CaseRecord("B", 121, True)]
    summary = summarize_cases(cases, target_seconds=120)
    assert summary["within_two_minutes_cases"] == 1
    summary = summarize_cases(cases, target_seconds=130)
    assert summary["within_two_minutes_cases"] == 2


def test_one_line_decision_summary_is_available():
    thresholds = GateThresholds(target_seconds=90, minimum_cases=30)
    result = build_command_summary(
        total_cases=30,
        within_two_minutes_rate=0.967,
        average_clearance_seconds=83.2,
        median_clearance_seconds=77.0,
        total_time_saved_minutes=412.5,
        total_savings_mnt=1234567,
        economic_measurement_cases=29,
        economic_coverage_rate=29 / 30,
        thresholds=thresholds,
    )
    assert result["decision"] == "GO"
    assert "30 case" in result["one_line"]
    assert "≤90 сек" in result["one_line"]
    assert "1,234,567" in result["one_line"]
