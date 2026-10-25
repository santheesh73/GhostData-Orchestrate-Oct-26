"""Measure real audits, abstentions and unpublishable candidates separately.

Reference labels are opened only after inference. This development module is
never imported by the prediction pipeline and never manufactures missing rows.
"""

from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from statistics import median
import time

from ghosttrace.emit.canonicalizer import canonical_steps
from ghosttrace.emit.operation_mapper import emit_decision
from ghosttrace.ingest.corpus import ingest_dataset
from ghosttrace.ingest.loader import load_evidence_catalog, load_requests
from ghosttrace.models import Authorization
from ghosttrace.policy.engine import PolicyEngine
from ghosttrace.policy.rulebook import RuleBook
from ghosttrace.quality.audit_gate import check_audit
from ghosttrace.quality.validator import OutputError, read_output, validate_rows
from ghosttrace.ingest.normalization import canonical_json
from .golden_diff import compare_rows


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def implementation_fingerprint():
    root = Path(__file__).resolve().parents[1]
    files = sorted(p for p in (root / "ghosttrace").rglob("*") if p.suffix in {".py", ".ps1", ".txt"})
    return hashlib.sha256(canonical_json([(p.relative_to(root).as_posix(), _sha(p)) for p in files]).encode()).hexdigest()


def audit_fingerprint(audits):
    """Include candidate plans and proofs, not just final (often empty) rows."""
    data = [asdict(audit) for audit in sorted(audits, key=lambda a: a.decision.request.case_id)]
    return hashlib.sha256(json.dumps(data, default=lambda value: value.isoformat(), sort_keys=True,
                                    ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def corpus_fingerprint(bundle):
    return hashlib.sha256(canonical_json(sorted((r.source.path, r.source_sha256)
        for r in (*bundle.files, *bundle.context))).encode()).hexdigest()


def run_audits(dataset_root, requests, *, with_extraction=False, cache_dir=None, cache_identity=True):
    """Inputs contain no expected outputs; model calls are disabled here."""
    started = time.perf_counter()
    bundle = ingest_dataset(dataset_root)
    extractor = None
    if with_extraction:
        from ghosttrace.extract.cache import ExtractionCache
        from ghosttrace.extract.engine import SelectiveExtractor
        from ghosttrace.extract.provider import ModelRunner
        from ghosttrace.extract.usage import UsageLedger
        cache = ExtractionCache(cache_dir or Path(dataset_root).parent / ".ghosttrace/extraction")
        extractor = SelectiveExtractor(cache, ModelRunner(None, cache, UsageLedger(), max_calls=0))
        bundle = extractor.enrich(bundle, dataset_root)
    ingested = time.perf_counter()
    engine = PolicyEngine(bundle.index, RuleBook.load(dataset_root),
                          extractor.resolve_intent if extractor else None, cache_identity=cache_identity)
    engine_built = time.perf_counter()
    audits = tuple(engine.audit(request) for request in sorted(requests, key=lambda r: r.case_id))
    finished = time.perf_counter()
    return bundle, engine, audits, {"ingestion_seconds": ingested - started,
        "engine_seconds": engine_built - ingested, "audit_seconds": finished - engine_built,
        "total_seconds": finished - started}, extractor


def benchmark_audits(dataset_root, requests_path, *, repetitions=3, with_extraction=False, cache_dir=None):
    if type(repetitions) is not int or not 3 <= repetitions <= 10:
        raise ValueError("benchmark requires 3 to 10 repetitions per configuration")
    requests = load_requests(requests_path)
    # One common untimed warm-up also prepares the frozen input bundle. No labels.
    bundle, _, warmup, timing, _ = run_audits(dataset_root, requests, with_extraction=with_extraction, cache_dir=cache_dir)
    rules = RuleBook.load(dataset_root)
    runs = {"reference": [], "cached_context": []}
    hashes = {audit_fingerprint(warmup)}
    for trial in range(repetitions):
        for cached in ((False, True) if trial % 2 == 0 else (True, False)):
            started = time.perf_counter()
            engine = PolicyEngine(bundle.index, rules, cache_identity=cached)
            built = time.perf_counter()
            audits = tuple(engine.audit(r) for r in sorted(requests, key=lambda r: r.case_id))
            finished = time.perf_counter()
            digest = audit_fingerprint(audits)  # Outside the timed interval.
            hashes.add(digest)
            runs["cached_context" if cached else "reference"].append({"trial": trial + 1,
                "engine_seconds": built - started, "audit_seconds": finished - built,
                "processing_seconds": finished - started, "audit_sha256": digest})
    if len(hashes) != 1:
        raise OutputError("reference and optimized audit proofs disagree; no speedup accepted")
    summary = {name: {key: {"median": median(r[key] for r in observations),
                           "minimum": min(r[key] for r in observations),
                           "maximum": max(r[key] for r in observations)}
                      for key in ("engine_seconds", "audit_seconds", "processing_seconds")}
               for name, observations in runs.items()}
    return {"scope": "LOCAL_OFFLINE_ALTERNATING_TRIALS", "request_count": len(requests),
            "repetitions_per_configuration": repetitions, "warmup_runs": 1,
            "mode": "EXTRACTION_AUGMENTED" if with_extraction else "STRUCTURED_ONLY",
            "excludes": ["startup", "ingestion", "fingerprint", "label_io"],
            "ingestion_seconds": timing["ingestion_seconds"], "runs": runs, "summary": summary,
            "processing_speedup": summary["reference"]["processing_seconds"]["median"] / summary["cached_context"]["processing_seconds"]["median"],
            "semantics_equal": True, "audit_sha256": next(iter(hashes)),
            "implementation_sha256": implementation_fingerprint(), "requests_sha256": _sha(requests_path),
            "corpus_sha256": corpus_fingerprint(bundle), "rules_sha256": _sha(Path(dataset_root) / "deletion_rules.csv"),
            "manifest_sha256": _sha(Path(dataset_root) / "evidence_files.csv"),
            "model_calls": 0, "output_written": False, "peak_memory": "NOT_MEASURED",
            "limits": "Local repeated measurements; not a universal speedup or accuracy claim."}


def candidate_steps(audit):
    return [step.as_dict() for step in canonical_steps(audit.candidate_operations)]


def step_probe(actual_by_case, expected):
    """Reuse the independent comparison's step logic without inventing statuses.

    Empty diagnostic statuses are deliberately discarded. These rows never
    reach a CSV writer or count toward published end-to-end metrics.
    """
    diagnostic = [{"case_id": case, "deletion_status": "", "steps_json": steps}
                  for case, steps in sorted(actual_by_case.items())]
    result = compare_rows(diagnostic, expected)
    keys = {"predicted_steps", "reference_steps", "step_true_positives", "step_precision", "step_recall",
            "step_f1", "correct_fields", "compared_fields", "field_accuracy", "exact_sequences", "sequence_accuracy"}
    return {"scope": "UNPUBLISHABLE_CANDIDATE_STEPS", **{key: result[key] for key in sorted(keys)}}


def stage_failures(audit, gate_errors):
    codes = {u.code for u in audit.decision.uncertainties}
    stages = set()
    if audit.intent.authorization == Authorization.UNRESOLVED:
        stages.add("AUTHORIZATION")
    if any("IDENTITY" in code or code == "SNAPSHOT_AVAILABILITY_UNKNOWN" for code in codes):
        stages.add("IDENTITY")
    if any("RESOURCE_LINK" in code or code == "NO_ASSESSED_RESOURCES" for code in codes):
        stages.add("RETRIEVAL_OR_LINKAGE")
    if "EVIDENCE_COVERAGE_NOT_ESTABLISHED" in codes:
        stages.add("COVERAGE")
    if any(code in codes for code in {"CONFLICTING_POLICY_FACTS", "RECORD_STATE_UNKNOWN", "FLOW_STATE_UNKNOWN", "RESTORE_STATE_UNKNOWN"}):
        stages.add("TEMPORAL_OR_STATE")
    if any(any(token in code for token in ("POLICY", "CATEGORY", "RETAINED", "IDENTIFIER_COVERAGE")) for code in codes):
        stages.add("POLICY_OR_INTERPRETATION")
    if any("COPY_ACTIONS" in code or "DEPENDENCY" in code for code in codes):
        stages.add("PLANNING")
    if gate_errors:
        stages.add("PUBLICATION_GATE")
    return sorted(stages)


def trace_audit(audit, engine):
    request = audit.decision.request
    gate = check_audit(audit, engine.observations)
    reconstruction = engine.reconstruction.reconstruct(request)
    observations = {o.observation_id: o for state in reconstruction.states for o in state.timeline}
    return {"case_id": request.case_id, "input": {"schema_valid": True, "text_omitted": True,
                "requested_at": request.requested_at.isoformat(), "audit_at": request.audit_at.isoformat()},
            "authorization": {"value": audit.intent.authorization.value, "reason": audit.intent.reason},
            "identity": {"status": reconstruction.identity.status, "candidate_count": len(reconstruction.identity.candidate_user_ids)},
            "retrieval": {"links": len(reconstruction.links), "state_scopes": len(reconstruction.states),
                          "excluded_future": reconstruction.excluded_future, "excluded_unknown_time": reconstruction.excluded_unknown_time,
                          "sources": sorted({o.evidence.evidence_id for o in observations.values()}),
                          "observation_ids": sorted(observations)},
            "model": {"calls": 0, "scope": "NATIVE_OFFLINE_TRACE"},
            "assessments": [{"system_id": a.resource.system_id, "resource_id": a.resource.resource_id,
                "physical_copy": a.resource.physical_copy, "category": a.category, "rule_id": a.rule_id,
                "action": a.action, "outcome": a.outcome, "observation_ids": a.observation_ids,
                "uncertainty_codes": [u.code for u in a.uncertainties]} for a in audit.assessments],
            "candidate_steps": candidate_steps(audit), "gate_errors": list(gate),
            "decision_status": audit.decision.status.value if audit.decision.status else None,
            "uncertainty_codes": sorted({u.code for u in audit.decision.uncertainties}),
            "writer": "NOT_CALLED", "output_written": False}


def evaluate_samples(dataset_root, requests_path, expected_path, *, with_extraction=False, cache_dir=None):
    request_sha = _sha(requests_path)
    requests = load_requests(requests_path)
    bundle, engine, audits, timing, extractor = run_audits(dataset_root, requests, with_extraction=with_extraction, cache_dir=cache_dir)
    rows, gates = [], {}
    for audit in audits:
        case = audit.decision.request.case_id
        gates[case] = check_audit(audit, engine.observations)
        if not gates[case]:
            rows.append(emit_decision(audit.decision).as_dict())
    # Label access deliberately happens only after every runtime audit and gate.
    expected = read_output(expected_path)
    # A deferred file still has a valid manifest ID. Citation existence/time
    # metadata and successful semantic extraction are different checks.
    catalog = load_evidence_catalog(dataset_root)
    publication_validation = validate_rows(rows, requests, catalog).as_dict()
    if not validate_rows(expected, requests, catalog).valid:
        raise OutputError("public reference fails the request/evidence contract")
    if request_sha != _sha(requests_path):
        raise OutputError("request source changed during evaluation")
    expected_by_case = {row["case_id"]: row for row in expected}
    cases = []
    for audit in audits:
        case = audit.decision.request.case_id
        truth = expected_by_case[case]
        expected_auth = Authorization.NON_DELETION if truth["deletion_status"] == "NOT_APPLICABLE" else Authorization.DELETION
        status = audit.decision.status.value if audit.decision.status else None
        cases.append({"case_id": case, "expected_status": truth["deletion_status"], "actual_status": status,
            "expected_authorization": expected_auth.value, "actual_authorization": audit.intent.authorization.value,
            "authorization_correct": audit.intent.authorization == expected_auth,
            "publishable": not gates[case], "status_correct": not gates[case] and status == truth["deletion_status"],
            "failure_stages": stage_failures(audit, gates[case]),
            "attribution": "UNRESOLVED_PIPELINE" if status is None else "OBSERVED_RESULT",
            "uncertainty_codes": sorted({u.code for u in audit.decision.uncertainties}),
            "gate_errors": list(gates[case]), "candidate_steps": candidate_steps(audit),
            "expected_steps": truth["steps_json"]})
    metrics = compare_rows(rows, expected)
    count = len(cases)
    features = {"request_count": count, "authorization_resolved": sum(a.intent.authorization != Authorization.UNRESOLVED for a in audits),
                "publishable_cases": len(rows), "abstained_cases": count - len(rows),
                "assessment_counts": dict(sorted(Counter(s.outcome for a in audits for s in a.assessments).items())),
                "failure_stage_counts": dict(sorted(Counter(stage for case in cases for stage in case["failure_stages"]).items())),
                "uncertainty_counts": dict(sorted(Counter(code for case in cases for code in case["uncertainty_codes"]).items())),
                "manifest_status_counts": dict(sorted(Counter(r.status.value for r in bundle.files).items())),
                "assessment_category_outcomes": dict(sorted(Counter((s.category or "UNMAPPED") + ":" + s.outcome
                    for a in audits for s in a.assessments).items())),
                "candidate_operation_counts": dict(sorted(Counter(op.operation for a in audits for op in a.candidate_operations).items())),
                "semantic_recall": "NOT_MEASURED"}
    digest = hashlib.sha256(canonical_json(cases).encode()).hexdigest()
    return {"scope": "PUBLIC_DEVELOPMENT_REFERENCE", "labels_previously_inspected": True, "held_out": False,
            "mode": "EXTRACTION_AUGMENTED" if with_extraction else "STRUCTURED_ONLY",
            "input_sha256": {"requests": request_sha, "expected": _sha(expected_path)},
            "corpus_sha256": corpus_fingerprint(bundle), "rules_sha256": _sha(Path(dataset_root) / "deletion_rules.csv"),
            "manifest_sha256": _sha(Path(dataset_root) / "evidence_files.csv"),
            "implementation_sha256": implementation_fingerprint(),
            "metrics": metrics, "publication_validation": publication_validation,
            "authorization_accuracy": sum(c["authorization_correct"] for c in cases) / count if count else None,
            "candidates": step_probe({a.decision.request.case_id: candidate_steps(a) for a in audits}, expected),
            "features": features, "cases": cases, "timing": timing, "semantic_sha256": digest,
            "usage": extractor.runner.ledger.summary() if extractor else {"calls": 0, "input_tokens": 0, "output_tokens": 0},
            "output_written": False, "submission_ready": False, "hidden_accuracy": "NOT_MEASURED"}
