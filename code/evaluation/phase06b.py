"""Offline source/root-cause and verification-coverage diagnostics; never predictions."""
from collections import Counter, defaultdict
from dataclasses import asdict
import argparse
import json
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
from evaluation.audit_evaluation import run_audits, candidate_steps, trace_audit, audit_fingerprint, step_probe
from evaluation.golden_diff import compare_rows
from ghosttrace.ingest.loader import load_requests
from ghosttrace.quality.validator import read_output
from ghosttrace.quality.audit_gate import check_audit
from ghosttrace.emit.operation_mapper import emit_decision
from ghosttrace.resolve.signals import payload, eligible
from ghosttrace.resolve.temporal_replay import extract_facts, replay
from ghosttrace.policy.facts import project, named
from ghosttrace.policy.obligations import condition

ROOT = CODE.parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / ".ghosttrace/phase06b/current")
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if not out.is_relative_to((ROOT / ".ghosttrace").resolve()):
        raise ValueError("raw diagnostic outputs must remain under .ghosttrace/")
    out.mkdir(parents=True, exist_ok=True)
    write = lambda name, value: (out / name).write_text(json.dumps(value, indent=2, default=lambda d: d.isoformat()) + "\n", encoding="utf-8")
    full_requests = load_requests(ROOT / "dataset/deletion_requests.csv")
    public_requests = load_requests(ROOT / "dataset/sample_deletion_requests.csv")
    full_ids = {r.case_id for r in full_requests}
    public_ids = {r.case_id for r in public_requests}
    bundle, engine, audits, timing, extractor = run_audits(ROOT / "dataset", (*full_requests, *public_requests),
        with_extraction=True, cache_dir=ROOT / ".ghosttrace/extraction")
    audits_by_case = {a.decision.request.case_id: a for a in audits}
    full = [a for a in audits if a.decision.request.case_id in full_ids]
    public = [a for a in audits if a.decision.request.case_id in public_ids]
    gates = {a.decision.request.case_id: check_audit(a, engine.observations) for a in audits}
    by_resource = defaultdict(list)
    for o in bundle.index.all_observations():
        if o.resource.resource_id:
            by_resource[(o.resource.system_id, o.resource.resource_id)].append(o)
    matrix, summaries = [], []
    for a in audits:
        q = a.decision.request
        summaries.append({"case_id": q.case_id, "status": a.decision.status.value if a.decision.status else None,
            "operations": candidate_steps(a), "coverage_blockers": a.coverage_blockers, "gate_errors": gates[q.case_id],
            "assessments": [{"system_id": s.resource.system_id, "resource_id": s.resource.resource_id,
                "copy": s.resource.physical_copy, "category": s.category, "outcome": s.outcome,
                "reasons": [u.code for u in s.uncertainties]} for s in a.assessments]})
        for s in a.assessments:
            if s.outcome != "UNKNOWN":
                continue
            raw = by_resource[(s.resource.system_id, s.resource.resource_id)]
            current = [o for o in raw if o.resource.physical_copy == s.resource.physical_copy and eligible(o, q.audit_at) == "ELIGIBLE"]
            states = replay(current, q.audit_at)
            facts = [asdict(f) for state in states for f in project(state)]
            rule = engine.rulebook.by_category.get(s.category)
            evaluated = [condition(rule, project(state), engine.reconstruction.graph.at(q.audit_at).resolve(q).user_id, q.audit_at)[0]
                         for state in states] if rule else []
            observations = [{"id": o.evidence.evidence_id, "observation_id": o.observation_id,
                "path": o.evidence.path, "locator": o.location, "observed_at": o.observed_at,
                "available_at": o.evidence.available_at, "derived_available_at": o.derived_available_at,
                "derived_valid_until": o.derived_valid_until,
                "copy": o.resource.physical_copy, "eligibility": eligible(o, q.audit_at),
                "claim_kind": o.claim_kind} for o in raw]
            codes = [u.code for u in s.uncertainties]
            stage = "POLICY_CONDITION_UNESTABLISHED"
            if any("LINK" in c for c in codes): stage = "RESOURCE_LINK_UNRESOLVED"
            elif not any(extract_facts(o) for o in current): stage = "SOURCE_FACT_MISSING"
            elif any("IDENTIFIER" in c for c in codes): stage = "UNSTRUCTURED_TEXT_UNINTERPRETED"
            elif any("CATEGORY" in c for c in codes): stage = "SOURCE_FACT_UNPARSED"
            elif any("RETAINED_RECORD" in c or "RECORD_STATE" in c for c in codes): stage = "SOURCE_FACT_MISSING"
            elif s.category == "SECURITY_AUDIT_LOG" and not any(f["dimension"].endswith("/retention_until") for f in facts): stage = "SOURCE_FACT_MISSING"
            matrix.append({"case_id": q.case_id, "subject": engine.reconstruction.graph.at(q.audit_at).resolve(q).user_id,
                "audit_at": q.audit_at, "system_id": s.resource.system_id, "resource_id": s.resource.resource_id,
                "physical_copy": s.resource.physical_copy, "category": s.category, "rule_id": s.rule_id,
                "required_action": s.action, "missing_conditions": codes, "known_facts": facts,
                "condition_text": rule.condition if rule else None,
                "condition_results": ["UNKNOWN" if v is None else "TRUE" if v else "FALSE" for v in evaluated],
                "observations": observations, "earliest_missing_stage": stage,
                "proposed_generalized_correction": ("Require an explicit effective retention interval; never infer one from presence/signature" if s.category == "SECURITY_AUDIT_LOG" else
                    "Recover source-scoped participant/order context separately from PII treatment" if s.category == "SUPPORT_MESSAGE" else
                    "Require explicit ownership, storage state or effective policy evidence for this exact resource"),
                "source_recovery_possible": "UNKNOWN; requires additional literal source support"})
        if gates[q.case_id] and not any(row["case_id"] == q.case_id for row in matrix):
            matrix.append({"case_id": q.case_id, "subject": engine.reconstruction.graph.at(q.audit_at).resolve(q).user_id,
                "audit_at": q.audit_at, "system_id": None, "resource_id": None, "physical_copy": None,
                "category": "CORPUS_COVERAGE", "rule_id": None, "required_action": None,
                "missing_conditions": list(a.coverage_blockers), "known_facts": [], "observations": [],
                "earliest_missing_stage": "RESOURCE_LINK_UNRESOLVED" if not a.assessments else "UNSTRUCTURED_TEXT_UNINTERPRETED",
                "source_recovery_possible": "UNKNOWN; resource-free or context-only evidence requires interpretation"})
    write("root-cause-matrix.json", matrix)
    write("all-audits.json", summaries)
    group = defaultdict(list)
    for row in matrix:
        if row["case_id"] in full_ids:
            group[(row["category"], row["earliest_missing_stage"])].append(row)
    ranked = [{"category": k[0], "mechanism": k[1], "distinct_cases": len({r["case_id"] for r in v}),
        "resources": len({(r["system_id"], r["resource_id"]) for r in v}),
        "physical_scopes": len({(r["case_id"], r["system_id"], r["resource_id"], r["physical_copy"]) for r in v})} for k, v in group.items()]
    ranked.sort(key=lambda r: (-r["distinct_cases"], r["category"]))
    write("ranked-causes.json", ranked)
    # Public labels are opened only after all production inference/gates above.
    expected = read_output(ROOT / "dataset/sample_output.csv")
    rows = [emit_decision(a.decision).as_dict() for a in public if not gates[a.decision.request.case_id]]
    metric = compare_rows(rows, expected)
    write("public.json", {"scope": "PUBLIC_DEVELOPMENT_REFERENCE", "metrics": metric,
        "candidate_metrics": step_probe({a.decision.request.case_id: candidate_steps(a) for a in public}, expected),
        "usage": extractor.runner.ledger.summary(), "output_written": False})
    verifications = []
    traces = []
    for a in public:
        q = a.decision.request
        reconstruction = engine.reconstruction.reconstruct(q)
        discovered = {(l.system_id, l.resource_id): l for l in reconstruction.links}
        trace = trace_audit(a, engine)
        traces.append(trace)
        truth = next(row for row in expected if row["case_id"] == q.case_id)
        for step in truth["steps_json"]:
            if step["phase"] != "VERIFICATION": continue
            key = step["system_id"], step["resource_id"]
            assessments = [s for s in a.assessments if (s.resource.system_id, s.resource.resource_id) == key]
            obs = by_resource[key]
            emitted = any(o.operation == step["operation"] and (o.system_id, o.resource_id) == key for o in a.candidate_operations)
            state = any(extract_facts(o) for o in obs if eligible(o, q.audit_at) == "ELIGIBLE")
            linked = key in discovered and discovered[key].status == "LINKED"
            established = bool(assessments) and all(s.outcome != "UNKNOWN" for s in assessments)
            earliest = ("SOURCE_FACT_MISSING" if not obs else "RESOURCE_LINK_UNRESOLVED" if not linked else
                "SOURCE_FACT_MISSING" if not state else "POLICY_CONDITION_UNESTABLISHED" if not established else
                "VERIFICATION_NOT_EMITTED" if not emitted else "SUPPORTED")
            verifications.append({"case_id": q.case_id, "reference_operation": step,
                "resource_discovered": bool(obs), "identity_linked": linked, "state_observed": state,
                "policy_condition_established": established, "assessment_created": bool(assessments),
                "planner_emitted": emitted, "earliest_missing_stage": earliest,
                "published": not gates[q.case_id]})
    write("public-traces.json", traces)
    write("verification-coverage.json", verifications)
    counts = {"statuses": dict(Counter(a.decision.status.value if a.decision.status else "UNRESOLVED" for a in full)),
        "unknown_scopes": dict(Counter((s.category or "UNMAPPED") + ":" + u.code for a in full for s in a.assessments if s.outcome == "UNKNOWN" for u in s.uncertainties)),
        "audit_sha256": audit_fingerprint(full), "timing_all550": timing,
        "usage": extractor.runner.ledger.summary(), "public_metrics": metric,
        "verification_stages": dict(Counter(r["earliest_missing_stage"] for r in verifications))}
    write("summary.json", counts)
    print(json.dumps({k: v for k, v in counts.items() if k not in {"public_metrics", "usage"}}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
