"""Development-only sample contract inspection. Never imported by pipeline.

Sample patterns are observations, not runtime rules or copied answer tables.
"""

from collections import Counter
from pathlib import Path

from .ingest.loader import load_requests
from .quality.validator import read_output, validate_rows


def inspect_samples(expected: Path, requests_path: Path, catalog) -> dict:
    rows = read_output(expected)
    report = validate_rows(rows, load_requests(requests_path), catalog)
    counts = Counter(step["operation"] for row in rows for step in row["steps_json"])
    return {"kind": "PUBLIC_SAMPLE_CONTRACT", "rows": len(rows),
            "steps": sum(counts.values()),
            "statuses": dict(sorted(Counter(r["deletion_status"] for r in rows).items())),
            "operation_counts": dict(sorted(counts.items())), "validation": report.as_dict(),
            "prediction_accuracy": "NOT_MEASURED"}
