from dataclasses import replace
from datetime import timedelta
from pathlib import Path
import re

import pytest

from fixtures.contract_cases import expected_demo_rows
from ghosttrace.quality.validator import ALLOWED, validate_rows
from ghosttrace.spec_registry import OPERATIONS

ROOT = Path(__file__).resolve().parents[2]


def test_producer_and_validator_match_official_table_independently():
    official = re.findall(r'\| `(FINDING|REMEDIATION|VERIFICATION)` \| `([^`]+)` \| `([^`]+)`',
                          (ROOT / "problem_statement.md").read_text(encoding="utf-8"))
    assert len(official) == 15
    assert [(op.phase, op.name, op.state) for op in OPERATIONS] == official
    assert list(ALLOWED) == official


def test_demo_matches_handwritten_expectations(rows, context):
    assert rows == expected_demo_rows()
    report = validate_rows(rows, context[0], context[2])
    assert report.valid
    assert report.as_dict()["semantic_support"] == "NOT_CHECKED"
    assert {s["operation"] for r in rows for s in r["steps_json"]} == {op.name for op in OPERATIONS}


@pytest.mark.parametrize("field,value,code", [
    ("step_no", True, "NUMBERING"), ("step_no", 0, "NUMBERING"),
    ("step_no", "1", "NUMBERING"), ("phase", "FINDING", "OPERATION_STATE"),
    ("state", "PRESENT", "OPERATION_STATE"), ("operation", "GUESS", "OPERATION"),
    ("system_id", "", "RESOURCE_ID"), ("resource_id", " x ", "RESOURCE_ID"),
    ("resource_id", [], "STEP_TYPES"), ("evidence_id", "", "CITATION_REQUIRED"),
    ("evidence_id", "missing", "CITATION_UNKNOWN"),
    ("resource_id", "bad\x00id", "STEP_TYPES"),
])
def test_rejects_mutated_step_fields(rows, context, field, value, code):
    rows[0]["steps_json"][0][field] = value
    assert code in {i.code for i in validate_rows(rows, context[0], context[2]).issues}


@pytest.mark.parametrize("mutation,code", [
    ("extra_field", "STEP_FIELDS"), ("missing_field", "STEP_FIELDS"),
    ("wrong_status", "STATUS"), ("empty_complete", "STATUS_PHASES"),
    ("nondeletion_steps", "STATUS_PHASES"), ("bad_steps_type", "STEPS_TYPE"),
    ("duplicate_case", "DUPLICATE_CASE"), ("missing_case", "CASE_COVERAGE"),
    ("extra_case", "CASE_COVERAGE"), ("case_order", "CASE_ORDER"),
    ("step_order", "ORDER"), ("extra_row_field", "ROW_FIELDS"),
    ("future_citation", "FUTURE_CITATION"), ("duplicate_step", "DUPLICATE_STEP"),
])
def test_rejects_contract_mutations(rows, context, mutation, code):
    first = rows[0]["steps_json"][0]
    if mutation == "extra_field": first["debug"] = "internal"
    elif mutation == "missing_field": del first["state"]
    elif mutation == "wrong_status": rows[0]["deletion_status"] = "UNKNOWN"
    elif mutation == "empty_complete": rows[0]["steps_json"] = []
    elif mutation == "nondeletion_steps": rows[2]["steps_json"] = [first]
    elif mutation == "bad_steps_type": rows[0]["steps_json"] = {}
    elif mutation == "duplicate_case": rows.append(rows[-1])
    elif mutation == "missing_case": rows.pop()
    elif mutation == "extra_case": rows.append({"case_id": "unexpected", "deletion_status": "NOT_APPLICABLE", "steps_json": []})
    elif mutation == "case_order": rows.reverse()
    elif mutation == "step_order": rows[0]["steps_json"].reverse()
    elif mutation == "extra_row_field": rows[0]["diagnostics"] = []
    elif mutation == "future_citation": rows[1]["steps_json"][5]["evidence_id"] = "synthetic_evidence"
    elif mutation == "duplicate_step": rows[0]["steps_json"].append(first.copy())
    assert code in {i.code for i in validate_rows(rows, context[0], context[2]).issues}


@pytest.mark.parametrize("operation", ["DELETE_RECORD", "VERIFY_RECORD_ABSENT", "REPORT_ACTIVE_DATA_FLOW"])
def test_rejects_incomplete_plan(rows, context, operation):
    steps = rows[1]["steps_json"]
    rows[1]["steps_json"] = [s for s in steps if s["operation"] != operation]
    for number, step in enumerate(rows[1]["steps_json"], 1): step["step_no"] = number
    assert "PLAN_COVERAGE" in {i.code for i in validate_rows(rows, context[0], context[2]).issues}


def test_citation_cutoff_is_inclusive(rows, context):
    catalog = context[2]
    assert validate_rows(rows, context[0], catalog).valid
    later = {key: replace(source, available_at=source.available_at + timedelta(seconds=1))
             for key, source in catalog.items()}
    assert "CITATION_TIME" in {i.code for i in validate_rows(rows, context[0], later).issues}


def test_missing_metadata_is_explicit(rows, context):
    report = validate_rows(rows, context[0])
    assert report.valid
    assert not report.evidence_metadata_checked
    assert report.as_dict()["semantic_support"] == "NOT_CHECKED"


def test_empty_or_duplicate_expected_input_is_not_valid(rows, context):
    assert not validate_rows([], []).valid
    assert "EXPECTED_CASES" in {i.code for i in validate_rows(rows, context[0] + context[0]).issues}
