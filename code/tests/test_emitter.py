from dataclasses import replace
import csv
import json
from pathlib import Path

import pytest

from ghosttrace.emit import canonicalizer, csv_writer
from ghosttrace.emit.operation_mapper import UnresolvedDecision, emit_decision
from ghosttrace.models import Authorization, Decision, DeletionStatus, Uncertainty
from ghosttrace.pipeline import publish_decisions
from ghosttrace.quality.validator import OutputError, read_output, validate_rows


def test_atomic_roundtrip_and_repeatability(tmp_path, context):
    output = tmp_path / "predictions.csv"
    requests, decisions, catalog = context
    publish_decisions(decisions, requests, catalog, output)
    first = output.read_bytes()
    assert len(read_output(output)) == 3
    assert b"\r\n" not in first
    publish_decisions(tuple(reversed(decisions)), requests, catalog, output)
    assert output.read_bytes() == first


def test_invalid_candidate_preserves_previous_bytes(tmp_path, context):
    requests, decisions, catalog = context
    output = tmp_path / "predictions.csv"
    output.write_bytes(b"previous-valid-artifact")
    corrupted = replace(decisions[0], operations=decisions[0].operations + decisions[0].operations[:1])
    with pytest.raises(ValueError): publish_decisions((corrupted, *decisions[1:]), requests, catalog, output)
    assert output.read_bytes() == b"previous-valid-artifact"
    assert not list(tmp_path.glob(".ghosttrace-*"))


def test_replace_failure_preserves_previous_and_cleans_staging(tmp_path, context, monkeypatch):
    output = tmp_path / "predictions.csv"
    output.write_bytes(b"old")
    def fail(*args): raise OSError("simulated replacement failure")
    monkeypatch.setattr(csv_writer.os, "replace", fail)
    with pytest.raises(OSError): publish_decisions(context[1], context[0], context[2], output)
    assert output.read_bytes() == b"old"
    assert not list(tmp_path.glob(".ghosttrace-*"))


@pytest.mark.parametrize("kind", ["unknown", "uncertainty", "coverage", "intent", "rationale", "nondeletion_operations"])
def test_mapper_refuses_unsupported_decisions(context, kind):
    decision = context[1][0]
    if kind == "unknown": decision = replace(decision, status=None)
    elif kind == "uncertainty": decision = replace(decision, uncertainties=(Uncertainty("MISSING", "not established"),))
    elif kind == "coverage": decision = replace(decision, coverage_complete=False)
    elif kind == "intent": decision = replace(decision, authorization=Authorization.NON_DELETION)
    elif kind == "rationale": decision = replace(decision, operations=(replace(decision.operations[0], rationale=""),))
    elif kind == "nondeletion_operations": decision = replace(decision, status=DeletionStatus.NOT_APPLICABLE,
                                                               authorization=Authorization.NON_DELETION)
    with pytest.raises(UnresolvedDecision): emit_decision(decision)


def test_batch_refuses_partial_or_changed_request_context(tmp_path, context):
    requests, decisions, catalog = context
    output = tmp_path / "prediction.csv"
    with pytest.raises(UnresolvedDecision): publish_decisions(decisions[:-1], requests, catalog, output)
    changed = replace(decisions[0], request=replace(requests[0], request_text="different context"))
    with pytest.raises(UnresolvedDecision): publish_decisions((changed, *decisions[1:]), requests, catalog, output)
    assert not output.exists()


def test_validator_detects_broken_producer_order(rows, context, monkeypatch):
    monkeypatch.setattr(canonicalizer, "OPERATION_RANK", {name: -rank for name, rank in canonicalizer.OPERATION_RANK.items()})
    broken = [emit_decision(d).as_dict() for d in context[1]]
    assert "ORDER" in {i.code for i in validate_rows(broken, context[0], context[2]).issues}


@pytest.mark.parametrize("json_value", [
    '{"not":"an array"}', '[1]', 'NaN', '[{"step_no":1,"step_no":2}]',
    '[{"state":NaN}]', '[',
])
def test_strict_json_reader_rejects_invalid_inputs(tmp_path, json_value):
    path = tmp_path / "output.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["synthetic", "COMPLETE", json_value])
    with pytest.raises(OutputError): read_output(path)


@pytest.mark.parametrize("content", [
    "", "case_id,steps_json,deletion_status\n", "case_id,deletion_status,steps_json\na,COMPLETE\n",
    'case_id,deletion_status,steps_json\na,COMPLETE,"unterminated',
])
def test_reader_rejects_csv_framing(tmp_path, content):
    path = tmp_path / "output.csv"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(OutputError): read_output(path)


def test_writer_refuses_official_dataset(context):
    root = Path(__file__).resolve().parents[2]
    with pytest.raises(ValueError):
        publish_decisions(context[1], context[0], context[2], root / "dataset/sample_output.csv")


def test_publication_requires_metadata(tmp_path, context):
    output = tmp_path / "predictions.csv"
    with pytest.raises(ValueError): publish_decisions(context[1], context[0], None, output)
    assert not output.exists()
