"""GHOSTTRACE contract and Phase 02 ingestion CLI; defaults resolve from this repo."""

import argparse
import json
from pathlib import Path
import sys

from ghosttrace.ingest.loader import InputError, load_evidence_catalog, load_requests
from ghosttrace.pipeline import diagnose_requests, publish_decisions
from ghosttrace.quality.validator import validate_file

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--validate-inputs-only", action="store_true")
    modes.add_argument("--validate-output", type=Path, metavar="CSV")
    modes.add_argument("--demo", action="store_true", help="compile synthetic decisions only")
    modes.add_argument("--ingest-evidence", action="store_true", help="parse/index evidence and report coverage only")
    parser.add_argument("--requests", type=Path, default=ROOT / "dataset/deletion_requests.csv")
    parser.add_argument("--dataset-root", type=Path, default=ROOT / "dataset")
    parser.add_argument("--output", type=Path, help="demo CSV, restricted to repository .ghosttrace/")
    args = parser.parse_args(argv)
    try:
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
        print(json.dumps(diagnose_requests(requests), indent=2))
        return 3
    except (InputError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc), "output_written": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
