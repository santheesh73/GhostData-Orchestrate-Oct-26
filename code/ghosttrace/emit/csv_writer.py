"""Validate first, stage bytes, recheck, then atomically publish a complete CSV."""

import csv
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping

from ..models import EvidenceSource, OutputRow, Request
from ..quality.validator import validate_file, validate_rows
from ..spec_registry import OUTPUT_COLUMNS


def write_output(rows: tuple[OutputRow, ...], destination: Path,
                 requests: tuple[Request, ...], catalog: Mapping[str, EvidenceSource]) -> Path:
    destination = Path(destination).resolve()
    dataset = Path(__file__).resolve().parents[3] / "dataset"
    if destination.suffix.lower() != ".csv" or destination.is_relative_to(dataset.resolve()):
        raise ValueError("output must be a CSV outside the preserved official dataset")
    if catalog is None:
        raise ValueError("publication requires an explicit evidence metadata catalog")
    ordered = tuple(sorted(rows, key=lambda row: row.case_id))
    report = validate_rows([row.as_dict() for row in ordered], requests, catalog)
    if not report.valid:
        raise ValueError("output validation failed: " + ",".join(sorted({i.code for i in report.issues})))
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=destination.parent, prefix=".ghosttrace-",
                                         suffix=".csv", delete=False) as stream:
            staging = Path(stream.name)
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(OUTPUT_COLUMNS)
            for row in ordered:
                payload = json.dumps([s.as_dict() for s in row.steps], ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False)
                writer.writerow((row.case_id, row.deletion_status, payload))
            stream.flush()
            os.fsync(stream.fileno())
        staged_report = validate_file(staging, requests, catalog)
        if not staged_report.valid:
            raise ValueError("serialized output failed independent validation")
        os.replace(staging, destination)
        return destination
    finally:
        if staging is not None and staging.exists():
            staging.unlink()
