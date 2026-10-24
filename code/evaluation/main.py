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
    parser.add_argument("--expected", type=Path, default=root / "dataset/sample_output.csv")
    parser.add_argument("--requests", type=Path, default=root / "dataset/sample_deletion_requests.csv")
    parser.add_argument("--dataset-root", type=Path, default=root / "dataset")
    args = parser.parse_args(argv)
    try:
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
