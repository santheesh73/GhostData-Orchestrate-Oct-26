"""GHOSTTRACE evidence audits and guarded full-dataset publication."""

import argparse
import json
from pathlib import Path
import sys

from ghosttrace.ingest.loader import InputError, load_evidence_catalog, load_requests
from ghosttrace.pipeline import diagnose_requests, publish_decisions, publish_policy_audits
from ghosttrace.emit.operation_mapper import UnresolvedDecision
from ghosttrace.quality.validator import validate_file

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--validate-inputs-only", action="store_true")
    modes.add_argument("--validate-output", type=Path, metavar="CSV")
    modes.add_argument("--demo", action="store_true", help="compile synthetic decisions only")
    modes.add_argument("--ingest-evidence", action="store_true", help="parse/index evidence and report coverage only")
    modes.add_argument("--reconstruct-evidence", action="store_true", help="resolve identity/history and report audit-time state coverage; no predictions")
    modes.add_argument("--audit-policy", action="store_true", help="audit authorization, policy obligations and risks; report unresolved coverage without writing predictions")
    modes.add_argument("--run", action="store_true", help="publish root output.csv only after all 518 official requests pass every audit and output check")
    modes.add_argument("--extract-evidence", action="store_true", help="selectively read documents/images and unresolved intent; no predictions")
    parser.add_argument("--with-extraction", action="store_true", help="augment --audit-policy with Phase 05 source extraction")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".ghosttrace/extraction")
    parser.add_argument("--max-model-calls", type=int, default=0, help="explicit opt-in paid-call budget 0..64; default 0")
    parser.add_argument("--requests", type=Path, default=ROOT / "dataset/deletion_requests.csv")
    parser.add_argument("--dataset-root", type=Path, default=ROOT / "dataset")
    parser.add_argument("--output", type=Path, help="demo CSV, restricted to repository .ghosttrace/")
    args = parser.parse_args(argv)
    try:
        if args.with_extraction and not (args.audit_policy or args.run):
            raise InputError("--with-extraction requires --audit-policy or --run")
        if args.max_model_calls and not (args.extract_evidence or args.with_extraction):
            raise InputError("model budget requires an explicit extraction mode")
        if args.demo:
            from ghosttrace.demo import synthetic_cases
            requests, decisions, catalog = synthetic_cases()
            destination = (args.output or ROOT / ".ghosttrace/phase01-demo.csv").resolve()
            if not destination.is_relative_to((ROOT / ".ghosttrace").resolve()):
                raise InputError("synthetic demo output must stay inside repository .ghosttrace/")
            result = publish_decisions(decisions, requests, catalog, destination)
            print(json.dumps({"phase": "01", "synthetic": True, "rows": len(requests),
                              "output": str(result), "production_accuracy": "NOT_MEASURED"}))
            return 0
        if args.output is not None:
            raise InputError("--output is supported only with --demo in Phase 01")
        if args.ingest_evidence:
            from ghosttrace.ingest.corpus import ingest_dataset
            bundle = ingest_dataset(args.dataset_root)
            print(json.dumps(bundle.summary(), indent=2))
            return 1 if bundle.has_errors else 0
        requests = load_requests(args.requests)
        if args.validate_inputs_only:
            print(json.dumps({"input_valid": True, "requests": len(requests),
                              "decision_status": "NOT_RUN", "output_written": False}))
            return 0
        if args.validate_output:
            report = validate_file(args.validate_output, requests, load_evidence_catalog(args.dataset_root))
            print(json.dumps(report.as_dict(), indent=2))
            return 0 if report.valid else 1
        if args.reconstruct_evidence:
            from ghosttrace.ingest.corpus import ingest_dataset
            from ghosttrace.resolve.engine import reconstruction_summary
            bundle = ingest_dataset(args.dataset_root)
            print(json.dumps(reconstruction_summary(bundle, requests), indent=2))
            return 1 if bundle.has_errors else 0
        if args.audit_policy or args.run:
            if args.run and (len(requests) != 518 or args.requests.resolve() != (ROOT / "dataset/deletion_requests.csv").resolve()
                             or args.dataset_root.resolve() != (ROOT / "dataset").resolve()):
                raise InputError("--run requires all 518 requests from the repository's official dataset paths")
            from ghosttrace.ingest.corpus import ingest_dataset
            from ghosttrace.policy.engine import audit_dataset, audit_summary
            from ghosttrace.policy.rulebook import RuleBook
            bundle = ingest_dataset(args.dataset_root)
            extractor = None
            if args.with_extraction:
                from ghosttrace.extract.engine import configured_extractor
                cache_root = (ROOT / ".ghosttrace").resolve()
                if not cache_root.is_relative_to(ROOT.resolve()) or not args.cache_dir.resolve().is_relative_to(cache_root):
                    raise InputError("extraction cache must stay in repository .ghosttrace/")
                extractor = configured_extractor(args.cache_dir, args.max_model_calls)
                bundle = extractor.enrich(bundle, args.dataset_root)
            audits = audit_dataset(bundle, RuleBook.load(args.dataset_root), requests,
                                   extractor.resolve_intent if extractor else None)
            report = audit_summary(bundle, audits)
            if extractor:
                report["phase"] = "05"
                report["extraction"] = extractor.summary()
            if args.run:
                report["publication_attempted"] = True
                if bundle.has_errors or report["unresolved_count"]:
                    report["publication_blocked"] = "INGESTION_OR_UNRESOLVED_AUDITS"
                else:
                    observations = {o.observation_id: o for o in bundle.index.all_observations()}
                    try:
                        result = publish_policy_audits(audits, requests, load_evidence_catalog(args.dataset_root),
                                                       ROOT / "output.csv", observations)
                    except UnresolvedDecision:
                        report["publication_blocked"] = "PROOF_GATE_FAILED"
                    else:
                        report["output_written"] = True
                        report["output"] = str(result)
            print(json.dumps(report, indent=2))
            return 1 if bundle.has_errors else 3 if report["unresolved_count"] or report.get("publication_blocked") else 0
        if args.extract_evidence:
            from ghosttrace.extract.engine import configured_extractor
            from ghosttrace.ingest.corpus import ingest_dataset
            from ghosttrace.policy.applicability import classify_request
            cache_root = (ROOT / ".ghosttrace").resolve()
            if not cache_root.is_relative_to(ROOT.resolve()) or not args.cache_dir.resolve().is_relative_to(cache_root):
                raise InputError("extraction cache must stay in repository .ghosttrace/")
            extractor = configured_extractor(args.cache_dir, args.max_model_calls)
            bundle = extractor.enrich(ingest_dataset(args.dataset_root), args.dataset_root)
            for request in requests:
                extractor.resolve_intent(request, classify_request(request.request_text))
            report = extractor.summary()
            report["indexed_observations"] = len(bundle.index)
            report["has_ingestion_errors"] = bundle.has_errors
            print(json.dumps(report, indent=2))
            return 1 if bundle.has_errors else 0
        print(json.dumps(diagnose_requests(requests), indent=2))
        return 3
    except (InputError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc), "output_written": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
