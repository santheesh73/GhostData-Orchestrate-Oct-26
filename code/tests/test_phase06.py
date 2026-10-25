from dataclasses import replace
from datetime import timedelta, timezone
import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ghosttrace.models import Authorization
from ghosttrace.policy.applicability import classify_request
from evaluation import audit_evaluation as evaluation
from evaluation.main import main as evaluation_cli
from fixtures.history_cases import at, change, observation, request, snapshot
from ghosttrace.ingest.evidence_index import EvidenceIndex
from ghosttrace.policy.engine import PolicyEngine
from ghosttrace.policy.rulebook import RuleBook
from ghosttrace.quality.validator import OutputError
from ghosttrace.resolve.engine import ReconstructionEngine, proof_fingerprint
from ghosttrace.resolve.identity_graph import IdentityGraph

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("text", [
    "I'm deleting my profile. Keep only anonymous totals.",
    "I am erasing my personal information.",
    "My profile has closed. Please remove that search result.",
    'The button says "Data bundle". Please delete the export file from my account.',
    "I want to close my account permanently.",
    "Close this account completely.",
    "I deleted my account. Could you verify that my profile is gone?",
    "My account failed to close. Please finish the deletion.",
    "I tried to erase my account. Please complete the erasure.",
    "Quiero eliminar mi cuenta. Pueden completar la eliminación?",
    "I no longer need this account. Please remove my contact details.",
])
def test_generalized_deletion_grammar(text):
    assert classify_request(text).authorization == Authorization.DELETION


@pytest.mark.parametrize("text,expected", [
    ('Example: "delete my profile"', Authorization.UNRESOLVED),
    ('The label says "Data bundle". Please export my account data.', Authorization.NON_DELETION),
    ("Do not close my account permanently.", Authorization.NON_DELETION),
    ("Could you tell me whether my account was removed?", Authorization.UNRESOLVED),
    ("Can you explain when my personal data is erased?", Authorization.UNRESOLVED),
    ("What account records can you delete?", Authorization.UNRESOLVED),
    ("I deleted my saved filter. Could you tell me whether my account was removed?", Authorization.UNRESOLVED),
    ("Someone said to delete my profile.", Authorization.UNRESOLVED),
    ("Please remove someone else's account.", Authorization.UNRESOLVED),
    ("Please reset the search filter on my profile.", Authorization.NON_DELETION),
    ("No completen la eliminación de mi cuenta.", Authorization.NON_DELETION),
    ("Please correct my name without removing any records.", Authorization.NON_DELETION),
])
def test_generalized_grammar_rejects_neighboring_non_authorizations(text, expected):
    assert classify_request(text).authorization == expected


@pytest.mark.parametrize("cutoff", [4, 9, 10, 12, 20, 22])
def test_cached_identity_matches_reference_at_every_temporal_boundary(cutoff):
    records = [snapshot(), snapshot("subject-B", "shared@example.invalid"),
        change(old="shared@example.invalid"),
        change("reuse", user="subject-B", old="b@example.invalid", new="shared@example.invalid", day=12),
        observation("pair", {"user_id": "subject-A", "email": "shared@example.invalid"}, day=4),
        observation("early-reference", {"customer_reference": "future-subject", "email": "shared@example.invalid"}, day=4),
        change("future-registry", user="future-subject", day=21)]
    req = request(email="shared@example.invalid", submitted=3, cutoff=cutoff)
    engines = [ReconstructionEngine(EvidenceIndex(records), cache_identity=cached) for cached in (False, True)]
    assert engines[0].graph.at(req.audit_at).resolve(req) == engines[1].graph.at(req.audit_at).resolve(req)
    assert proof_fingerprint(engines[0].reconstruct(req)) == proof_fingerprint(engines[1].reconstruct(req))


def test_cached_context_is_immutable_and_does_not_promote_missing_capture_clock():
    graph = IdentityGraph([snapshot(email="old@example.invalid"), change(day=21)])
    with pytest.raises(TypeError):
        graph.context_aliases[("email", "old@example.invalid")] = ()
    graph.at(at(22))  # Warm a later view first; no cross-cutoff ownership cache.
    early = graph.at(at(20)).resolve(request())
    assert early.status == "CONTEXT_ONLY"
    assert {u.code for u in early.uncertainties} == {"SNAPSHOT_AVAILABILITY_UNKNOWN"}
    assert all(o.basis == "SNAPSHOT_CONTEXT" and not o.certain for o in early.ownership)


@pytest.mark.parametrize("user,resource,case", [
    ("urn:subject:alpha", "opaque/resource", "arbitrary-case"),
    ("random-785", "no-numeric-family", "case/no-template"),
    ("customer@internal-id", "漢字-record", "Ω-case"),
])
def test_policy_metamorphic_ids_order_clocks_and_future_noise(user, resource, case):
    records = [change(user=user), observation("retained-copy", {
        "record_type": "USER_PROFILE", "subject_reference": user, "email": "old@example.invalid"}, resource=resource)]
    req = request(case=case)
    rules = RuleBook.load(ROOT / "dataset")
    def run(items, selected=req):
        return PolicyEngine(EvidenceIndex(items), rules).audit(selected, coverage_complete=True)
    baseline = run(records)
    assert baseline.decision.status.value == "INCOMPLETE"
    assert [op.operation for op in baseline.decision.operations] == ["REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT"]
    assert all(op.resource_id == resource for op in baseline.decision.operations)
    future = observation("future", {"record_type": "USER_PROFILE", "subject_reference": user,
                                    "email": None, "result": "NOT_FOUND"}, day=21, resource=resource)
    assert baseline == run([future, *records[::-1]])
    offset = timezone(timedelta(hours=5, minutes=30))
    shifted = replace(req, requested_at=req.requested_at.astimezone(offset),
                      reported_at=req.reported_at.astimezone(offset), audit_at=req.audit_at.astimezone(offset))
    assert baseline == run(records, shifted)
    reference = PolicyEngine(EvidenceIndex(records), rules, cache_identity=False).audit(req, coverage_complete=True)
    assert baseline == reference


def test_candidate_plan_fingerprint_detects_a_deliberately_broken_optimization():
    rules = RuleBook.load(ROOT / "dataset")
    records = [change(), observation("present", {"record_type": "USER_PROFILE", "subject_reference": "subject-A"})]
    result = PolicyEngine(EvidenceIndex(records), rules).audit(request())
    assert result.decision.status is None and result.candidate_operations
    assert evaluation.audit_fingerprint([result]) != evaluation.audit_fingerprint([replace(result, candidate_operations=())])


def test_real_public_evaluation_counts_abstentions_and_reads_labels_after_gates(monkeypatch):
    events = []
    original_run, original_gate, original_read = evaluation.run_audits, evaluation.check_audit, evaluation.read_output
    def run(*args, **kwargs):
        result = original_run(*args, **kwargs)
        events.append("inference-complete")
        return result
    def gate(*args):
        assert events[0] == "inference-complete" and "labels" not in events
        events.append("gate")
        return original_gate(*args)
    def read(*args):
        assert events == ["inference-complete", *(["gate"] * 32)]
        events.append("labels")
        return original_read(*args)
    monkeypatch.setattr(evaluation, "run_audits", run)
    monkeypatch.setattr(evaluation, "check_audit", gate)
    monkeypatch.setattr(evaluation, "read_output", read)
    report = evaluation.evaluate_samples(ROOT / "dataset", ROOT / "dataset/sample_deletion_requests.csv", ROOT / "dataset/sample_output.csv")
    assert report["held_out"] is False and report["labels_previously_inspected"] is True
    assert report["metrics"]["reference_cases"] == 32
    assert report["metrics"]["predicted_cases"] == 0
    assert report["metrics"]["status_accuracy"] == report["metrics"]["field_accuracy"] == 0
    assert report["metrics"]["step_precision"] is None
    assert report["features"]["abstained_cases"] == 32
    assert report["candidates"]["scope"] == "UNPUBLISHABLE_CANDIDATE_STEPS"
    assert report["candidates"]["step_true_positives"] == 9
    assert report["candidates"]["step_recall"] < .05
    assert report["submission_ready"] is report["output_written"] is False
    assert all(len(value) == 64 for value in report["input_sha256"].values())
    # The manifest includes deferred PDFs/images; their reference citations
    # remain contract-valid even without semantic extraction.
    assert report["features"]["manifest_status_counts"]["DEFERRED"] == 15


def test_trace_omits_subject_text_and_uses_actual_gate_proofs():
    engine = PolicyEngine(EvidenceIndex([change(), observation("present", {
        "record_type": "USER_PROFILE", "subject_reference": "subject-A"})]), RuleBook.load(ROOT / "dataset"))
    audit = engine.audit(request())
    trace = evaluation.trace_audit(audit, engine)
    encoded = json.dumps(trace)
    assert "old@example.invalid" not in encoded and "subject-A" not in encoded and "Delete my account" not in encoded
    assert trace["identity"]["status"] == "RESOLVED"
    assert trace["retrieval"]["observation_ids"]
    assert trace["candidate_steps"] and trace["gate_errors"]
    assert trace["writer"] == "NOT_CALLED" and trace["output_written"] is False


def test_step_probe_never_turns_candidates_into_status_predictions(rows):
    result = evaluation.step_probe({r["case_id"]: r["steps_json"] for r in rows}, rows)
    assert result["step_f1"] == 1
    assert "status_accuracy" not in result and "exact_row_accuracy" not in result
    with pytest.raises(OutputError):
        evaluation.step_probe({}, [])


@pytest.mark.parametrize("repetitions", [0, 2, 11, True])
def test_benchmark_rejects_invalid_trial_counts(repetitions):
    with pytest.raises(ValueError):
        evaluation.benchmark_audits(None, None, repetitions=repetitions)


def test_benchmark_alternates_order_and_checks_all_audit_fields(monkeypatch):
    records = [change(), observation("record", {"record_type": "USER_PROFILE", "subject_reference": "subject-A"})]
    rules = RuleBook.load(ROOT / "dataset")
    bundle = SimpleNamespace(index=EvidenceIndex(records), files=(), context=())
    real_engine = PolicyEngine
    warmup = real_engine(bundle.index, rules).audit(request())
    monkeypatch.setattr(evaluation, "load_requests", lambda _: (request(),))
    monkeypatch.setattr(evaluation, "run_audits", lambda *a, **k: (bundle, None, (warmup,), {"ingestion_seconds": 0}, None))
    monkeypatch.setattr(evaluation.RuleBook, "load", lambda _: rules)
    monkeypatch.setattr(evaluation, "_sha", lambda _: "a" * 64)
    order = []
    def factory(*args, **kwargs):
        order.append(kwargs["cache_identity"])
        return real_engine(*args, **kwargs)
    monkeypatch.setattr(evaluation, "PolicyEngine", factory)
    report = evaluation.benchmark_audits(ROOT / "dataset", None)
    assert order == [False, True, True, False, False, True]
    assert report["semantics_equal"] is True and report["request_count"] == 1
    assert len(report["runs"]["reference"]) == len(report["runs"]["cached_context"]) == 3
    class Broken:
        def audit(self, req):
            return replace(warmup, candidate_operations=())
    monkeypatch.setattr(evaluation, "PolicyEngine", lambda *a, **k: Broken())
    with pytest.raises(OutputError, match="proofs disagree"):
        evaluation.benchmark_audits(ROOT / "dataset", None)


def test_evaluation_cli_rejects_cache_escape_and_unknown_trace(capsys, tmp_path):
    assert evaluation_cli(["--audit-samples", "--with-extraction", "--cache-dir", str(tmp_path)]) == 2
    assert "cache" in capsys.readouterr().err
    assert evaluation_cli(["--trace-case", "nonexistent-case"]) == 2
    assert "matching case" in capsys.readouterr().err


def test_all_inference_modules_remain_independent_of_evaluation_labels():
    for path in (ROOT / "code/ghosttrace").rglob("*.py"):
        if path.name == "contract_mining.py":
            continue  # Explicit development-only public-reference inspector.
        text = path.read_text(encoding="utf-8")
        assert "sample_output.csv" not in text
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("evaluation")
                assert "contract_mining" not in (node.module or "")
            elif isinstance(node, ast.Import):
                assert all(not name.name.startswith("evaluation") for name in node.names)
