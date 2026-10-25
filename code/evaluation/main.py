"""Development CLI for public sample inspection and candidate comparison."""

import argparse
import json
from pathlib import Path
import sys

# Bootstrap only our own code tree; no dependency on the caller's directory.
CODE = Path(__file__).resolve().parent.parent
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from evaluation.golden_diff import compare_files
from ghosttrace.contract_mining import inspect_samples
from ghosttrace.ingest.loader import InputError, load_evidence_catalog, load_requests
from ghosttrace.quality.validator import OutputError, validate_file


def main(argv=None) -> int:
    root = CODE.parent
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--inspect-samples", action="store_true")
    modes.add_argument("--predictions", type=Path)
    modes.add_argument("--ingestion-coverage", action="store_true")
    modes.add_argument("--audit-samples", action="store_true", help="run blind audits, then compare with public reference; no prediction output")
    modes.add_argument("--trace-case", help="trace one selected request without opening labels")
    modes.add_argument("--benchmark-audits", action="store_true", help="compare reference and cached identity contexts; no labels/output")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--with-extraction", action="store_true")
    parser.add_argument("--cache-dir", type=Path, default=root / ".ghosttrace/extraction")
    parser.add_argument("--expected", type=Path, default=root / "dataset/sample_output.csv")
    parser.add_argument("--requests", type=Path, default=root / "dataset/sample_deletion_requests.csv")
    parser.add_argument("--dataset-root", type=Path, default=root / "dataset")
    args = parser.parse_args(argv)
    try:
        if args.with_extraction:
            cache_root = (root / ".ghosttrace").resolve()
            if not cache_root.is_relative_to(root.resolve()) or not args.cache_dir.resolve().is_relative_to(cache_root):
                raise InputError("extraction caches must remain under repository .ghosttrace/")
        if args.benchmark_audits:
            from evaluation.audit_evaluation import benchmark_audits
            result = benchmark_audits(args.dataset_root, args.requests, repetitions=args.repetitions,
                                      with_extraction=args.with_extraction, cache_dir=args.cache_dir)
            print(json.dumps(result, indent=2))
            return 0
        if args.audit_samples or args.trace_case:
            from evaluation.audit_evaluation import evaluate_samples, run_audits, trace_audit
            if args.audit_samples:
                result = evaluate_samples(args.dataset_root, args.requests, args.expected,
                                          with_extraction=args.with_extraction, cache_dir=args.cache_dir, prediction_defaults=True)
                print(json.dumps(result, indent=2))
                return 0 if result["metrics"]["exact_row_accuracy"] == 1 else 1
            requests = tuple(r for r in load_requests(args.requests) if r.case_id == args.trace_case)
            if len(requests) != 1:
                raise InputError("trace requires exactly one matching case ID")
            _, engine, audits, _, _ = run_audits(args.dataset_root, requests, with_extraction=args.with_extraction, cache_dir=args.cache_dir)
            print(json.dumps(trace_audit(audits[0], engine), indent=2))
            return 0
        if args.ingestion_coverage:
            from ghosttrace.ingest.corpus import ingest_dataset
            from evaluation.coverage import coverage_metrics
            bundle = ingest_dataset(args.dataset_root)
            print(json.dumps(coverage_metrics(bundle), indent=2))
            return 1 if bundle.has_errors else 0
        catalog = load_evidence_catalog(args.dataset_root)
        if args.inspect_samples:
            result = inspect_samples(args.expected, args.requests, catalog)
            print(json.dumps(result, indent=2))
            return 0 if result["validation"]["contract_valid"] else 1
        requests = load_requests(args.requests)
        reference_report = validate_file(args.expected, requests, catalog)
        if not reference_report.valid:
            raise OutputError("reference output fails the supplied contract context")
        report = validate_file(args.predictions, requests, catalog)
        result = compare_files(args.predictions, args.expected)
        result["candidate_validation"] = report.as_dict()
        print(json.dumps(result, indent=2))
        return 0 if report.valid and result["exact_rows"] == result["reference_cases"] else 1
    except (InputError, OutputError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "accuracy": "NOT_MEASURED"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
