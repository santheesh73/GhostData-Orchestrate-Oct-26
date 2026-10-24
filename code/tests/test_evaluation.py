from copy import deepcopy

import pytest

from evaluation.golden_diff import compare_rows
from fixtures.contract_cases import expected_demo_rows
from ghosttrace.quality.validator import OutputError


def test_synthetic_comparison_against_independent_expectations(rows):
    report = compare_rows(rows, expected_demo_rows())
    assert report["reference_cases"] == report["exact_rows"] == 3
    assert report["reference_steps"] == report["step_true_positives"] == 21
    assert report["exact_row_accuracy"] == report["field_accuracy"] == 1
    assert report["failures"] == []


def test_status_error_does_not_hide_correct_sequence(rows):
    changed = deepcopy(rows)
    changed[0]["deletion_status"] = "INCOMPLETE"
    result = compare_rows(changed, rows)
    assert result["status_correct"] == result["exact_rows"] == 2
    assert result["exact_sequences"] == 3
    assert "STATUS" in result["failures"][0]["categories"]


def test_dropped_step_does_not_shift_field_alignment(rows):
    changed = deepcopy(rows)
    changed[0]["steps_json"].pop(0)
    result = compare_rows(changed, rows)
    assert result["step_true_positives"] == 20
    assert result["correct_fields"] == 20 * 7
    assert result["compared_fields"] == 21 * 7
    assert "MISSING_STEP" in result["failures"][0]["categories"]


def test_wrong_evidence_is_detected_as_field_and_step_error(rows):
    changed = deepcopy(rows)
    changed[0]["steps_json"][0]["evidence_id"] = "wrong"
    result = compare_rows(changed, rows)
    assert result["correct_fields"] == 21 * 7 - 1
    assert result["step_true_positives"] == 20


def test_numbering_is_separate_from_step_set_metrics(rows):
    changed = deepcopy(rows)
    changed[0]["steps_json"][0]["step_no"] = 99
    result = compare_rows(changed, rows)
    assert result["step_f1"] == 1
    assert result["sequence_accuracy"] == 2 / 3
    assert result["field_accuracy"] < 1


def test_missing_and_extra_cases_are_explicit(rows):
    changed = deepcopy(rows[1:])
    changed.append({"case_id": "extra", "deletion_status": "NOT_APPLICABLE", "steps_json": []})
    result = compare_rows(changed, rows)
    assert result["missing_cases"] == ["synthetic_complete"]
    assert result["extra_cases"] == ["extra"]
    assert result["exact_rows"] == 2


def test_zero_step_denominators_are_not_invented():
    row = {"case_id": "synthetic_none", "deletion_status": "NOT_APPLICABLE", "steps_json": []}
    result = compare_rows([row], [row])
    assert result["exact_rows"] == 1
    assert result["field_accuracy"] is result["step_f1"] is None


def test_duplicate_predictions_and_missing_reference_are_rejected(rows):
    with pytest.raises(OutputError): compare_rows(rows + [rows[0]], rows)
    with pytest.raises(OutputError): compare_rows(rows, [])


def test_json_object_field_order_does_not_affect_comparison(rows):
    changed = deepcopy(rows)
    for row in changed:
        row["steps_json"] = [dict(reversed(list(s.items()))) for s in row["steps_json"]]
    assert compare_rows(changed, rows)["exact_rows"] == 3
