"""Public-reference comparison; no hidden labels or prediction logic.

Step set metrics exclude numbering; exact sequence retains every field. Field
alignment uses phase/system/resource/operation, so one dropped step does not
shift all later comparisons. Extra/missing steps contribute seven wrong fields.
Metrics with no supported denominator are null, never an invented score.
"""

from collections import Counter, defaultdict
from itertools import zip_longest
from pathlib import Path

from ghosttrace.quality.validator import OutputError, read_output
from . import failure_taxonomy as failure

FIELDS = ("step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id")
ALIGNMENT = ("phase", "system_id", "resource_id", "operation")


def _index(rows: list[dict]) -> dict[str, dict]:
    indexed = {}
    for row in rows:
        if type(row) is not dict or set(row) != {"case_id", "deletion_status", "steps_json"}:
            raise OutputError("comparison requires exact output row fields")
        if type(row["case_id"]) is not str or not row["case_id"] or row["case_id"] in indexed:
            raise OutputError("comparison requires unique nonempty case IDs")
        if type(row["deletion_status"]) is not str or type(row["steps_json"]) is not list:
            raise OutputError("comparison requires string statuses and step arrays")
        for step in row["steps_json"]:
            if type(step) is not dict or set(step) != set(FIELDS):
                raise OutputError("comparison requires all seven step fields")
            if type(step["step_no"]) is not int or any(type(step[k]) is not str for k in FIELDS[1:]):
                raise OutputError("comparison requires typed step fields")
        indexed[row["case_id"]] = row
    return indexed


def _groups(steps):
    groups = defaultdict(list)
    for step in steps:
        groups[tuple(step[k] for k in ALIGNMENT)].append(step)
    return groups


def compare_rows(actual: list[dict], expected: list[dict]) -> dict:
    actual_index, expected_index = _index(actual), _index(expected)
    if not expected_index:
        raise OutputError("cannot estimate accuracy without reference cases")
    correct_status = exact_rows = exact_sequences = true_positive = 0
    predicted_steps = reference_steps = correct_fields = field_total = 0
    failures = []
    for case_id in sorted(set(actual_index) | set(expected_index)):
        prediction, reference = actual_index.get(case_id), expected_index.get(case_id)
        categories = []
        if reference is None:
            categories.append(failure.ROW_EXTRA)
        elif prediction is None:
            categories.append(failure.ROW_MISSING)
        else:
            if prediction["deletion_status"] == reference["deletion_status"]:
                correct_status += 1
            else:
                categories.append(failure.STATUS)
            if prediction == reference:
                exact_rows += 1
            if prediction["steps_json"] == reference["steps_json"]:
                exact_sequences += 1
            else:
                categories.append(failure.SEQUENCE)
        predicted = prediction["steps_json"] if prediction else []
        truth = reference["steps_json"] if reference else []
        predicted_steps += len(predicted)
        reference_steps += len(truth)
        p_counter = Counter(tuple(s[k] for k in FIELDS[1:]) for s in predicted)
        r_counter = Counter(tuple(s[k] for k in FIELDS[1:]) for s in truth)
        true_positive += sum((p_counter & r_counter).values())
        if r_counter - p_counter:
            categories.append(failure.MISSING_STEP)
        if p_counter - r_counter:
            categories.append(failure.EXTRA_STEP)
        p_groups, r_groups = _groups(predicted), _groups(truth)
        case_wrong_fields = 0
        for key in sorted(set(p_groups) | set(r_groups)):
            for left, right in zip_longest(p_groups[key], r_groups[key]):
                field_total += len(FIELDS)
                if left is not None and right is not None:
                    matches = sum(left[k] == right[k] for k in FIELDS)
                    correct_fields += matches
                    case_wrong_fields += len(FIELDS) - matches
                else:
                    case_wrong_fields += len(FIELDS)
        if case_wrong_fields:
            categories.append(failure.FIELD)
        if categories:
            failures.append({"case_id": case_id, "categories": sorted(set(categories))})
    cases = len(expected_index)
    denominator = predicted_steps + reference_steps
    return {
        "reference_cases": cases, "predicted_cases": len(actual_index),
        "missing_cases": sorted(set(expected_index) - set(actual_index)),
        "extra_cases": sorted(set(actual_index) - set(expected_index)),
        "status_correct": correct_status, "status_accuracy": correct_status / cases,
        "exact_rows": exact_rows, "exact_row_accuracy": exact_rows / cases,
        "exact_sequences": exact_sequences, "sequence_accuracy": exact_sequences / cases,
        "predicted_steps": predicted_steps, "reference_steps": reference_steps,
        "step_true_positives": true_positive,
        "step_precision": true_positive / predicted_steps if predicted_steps else None,
        "step_recall": true_positive / reference_steps if reference_steps else None,
        "step_f1": 2 * true_positive / denominator if denominator else None,
        "correct_fields": correct_fields, "compared_fields": field_total,
        "field_accuracy": correct_fields / field_total if field_total else None,
        "failures": failures, "hidden_accuracy": "NOT_MEASURED",
    }


def compare_files(actual: Path, expected: Path) -> dict:
    return compare_rows(read_output(actual), read_output(expected))
