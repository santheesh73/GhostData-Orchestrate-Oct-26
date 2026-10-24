import csv
from pathlib import Path

import pytest

from ghosttrace.ingest.loader import InputError, load_evidence_catalog, load_requests, parse_timestamp
from ghosttrace.spec_registry import REQUEST_COLUMNS

ROOT = Path(__file__).resolve().parents[2]


def test_actual_inputs_and_metadata_load_without_evidence_inference():
    assert len(load_requests(ROOT / "dataset/deletion_requests.csv")) == 518
    assert len(load_requests(ROOT / "dataset/sample_deletion_requests.csv")) == 32
    assert len(load_evidence_catalog(ROOT / "dataset")) == 94 + 4011 + 306


@pytest.mark.parametrize("value", ["", "2026-01-01", "2026-01-01T00:00:00", "invalid", "2026-02-30T00:00:00Z"])
def test_rejects_ambiguous_or_bad_times(value):
    with pytest.raises(InputError): parse_timestamp(value, "time")


def test_timezones_normalize_to_utc():
    assert parse_timestamp("2026-01-01T05:30:00+05:30", "t") == parse_timestamp("2026-01-01T00:00:00Z", "t")


@pytest.mark.parametrize("kind", ["empty", "duplicate", "ragged", "blank", "bad_status", "header", "nul", "padded"])
def test_request_input_defects(tmp_path, kind):
    path = tmp_path / "requests.csv"
    values = ["opaque_01", "person@example.invalid", "2026-01-01T00:00:00Z", "NOT_STARTED",
              "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", "Please delete"]
    if kind == "blank": values[-1] = ""
    if kind == "bad_status": values[3] = "DELETED"
    if kind == "nul": values[-1] += "\x00"
    if kind == "padded": values[0] = " opaque_01"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(REQUEST_COLUMNS if kind != "header" else tuple(reversed(REQUEST_COLUMNS)))
        if kind != "empty": writer.writerow(values[:-1] if kind == "ragged" else values)
        if kind == "duplicate": writer.writerow(values)
    with pytest.raises(InputError): load_requests(path)


def test_request_ids_and_multilingual_text_are_preserved(tmp_path):
    path = tmp_path / "requests.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(REQUEST_COLUMNS)
        writer.writerow(["0001", "person@example.invalid", "2026-01-01T00:00:00Z", "NOT_STARTED",
                         "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", "Supprimez, s’il vous plaît\nMerci"])
    request = load_requests(path)[0]
    assert request.case_id == "0001"
    assert request.request_text == "Supprimez, s’il vous plaît\nMerci"
