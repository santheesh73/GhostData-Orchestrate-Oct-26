"""Extraction accounting, not ground-truth recall or deletion accuracy."""

from collections import Counter

from ghosttrace.ingest.normalization import ParseStatus


def coverage_metrics(bundle):
    structured = [r for r in bundle.files if r.format in {"json", "sql", "log", "text", "csv"}]
    parsed = sum(r.status == ParseStatus.PARSED for r in structured)
    return {"scope": "PARSING_COVERAGE", "manifest_files": len(bundle.files),
            "structured_files": len(structured), "fully_parsed_structured_files": parsed,
            "structured_file_parse_rate": parsed / len(structured) if structured else None,
            "deferred_files": sum(r.status == ParseStatus.DEFERRED for r in bundle.files),
            "manifest_formats": dict(sorted(Counter(r.format for r in bundle.files).items())),
            "diagnostic_counts": dict(sorted(Counter(
                [d.code for r in (*bundle.files, *bundle.context) for d in r.diagnostics]
                + [d.code for d in bundle.diagnostics]).items())),
            "identity_accuracy": "NOT_MEASURED", "evidence_recall": "NOT_MEASURED",
            "deletion_accuracy": "NOT_MEASURED", "has_ingestion_errors": bundle.has_errors}
