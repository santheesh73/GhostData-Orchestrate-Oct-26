from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from evaluation.coverage import coverage_metrics
from ghosttrace.ingest.corpus import ingest_dataset
from ghosttrace.ingest.normalization import ParseStatus
from ghosttrace.ingest.structured_parser import load_context_sources, load_manifest
from ghosttrace.ingest import structured_parser
from ghosttrace.ingest.loader import InputError
from ghosttrace.models import EvidenceSource
from ghosttrace.quality.validator import validate_rows

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def actual_bundle():
    return ingest_dataset(ROOT / "dataset")


def write_csv(path, columns, records):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def context_fixture(root):
    timestamp = "2026-01-01T00:00:00Z"
    write_csv(root / "user_identities.csv", ["user_id", "name", "email", "phone", "email_hash", "updated_at"],
              [dict(user_id="opaque_subject", name="Synthetic", email="new@example.invalid", phone="", email_hash="", updated_at=timestamp)])
    write_csv(root / "user_audit_log.csv", ["audit_id", "user_id", "event_time", "field_name", "old_value", "new_value"],
              [dict(audit_id="synthetic_audit", user_id="opaque_subject", event_time=timestamp, field_name="email",
                    old_value="old@example.invalid", new_value="new@example.invalid")])
    write_csv(root / "system_activity.csv", ["activity_id", "event_time", "event_type", "source_system", "target_system", "resource_id", "reported_result", "details"],
              [dict(activity_id="synthetic_activity", event_time=timestamp, event_type="DELETE_RECORD", source_system="worker",
                    target_system="svc", resource_id="opaque_resource", reported_result="SUCCESS", details="Reported claim")])
    write_csv(root / "deletion_rules.csv", ["rule_id", "data_category", "condition", "required_action"],
              [dict(rule_id="synthetic_rule", data_category="PROFILE", condition="Always", required_action="DELETE")])


def test_actual_corpus_has_total_accounting_and_no_silent_structured_omissions(actual_bundle):
    assert len(actual_bundle.files) == 94
    assert Counter(r.status for r in actual_bundle.files) == {ParseStatus.PARSED: 79, ParseStatus.DEFERRED: 15}
    assert all(r.status == ParseStatus.PARSED for r in actual_bundle.context)
    assert sum(len(r.observations) for r in actual_bundle.context) == 850 + 306 + 4011 + 15
    assert not actual_bundle.has_errors
    assert all(len(r.source_sha256) == 64 for r in actual_bundle.files)
    assert all(o.observation_id and o.location and o.source_sha256 for o in actual_bundle.index.all_observations())
    assert all(r.units_seen == r.units_parsed for r in actual_bundle.files if r.status == ParseStatus.PARSED)


def test_observation_provenance_hashes_match_actual_source_bytes(actual_bundle):
    for result in (*actual_bundle.files, *actual_bundle.context):
        expected = hashlib.sha256((ROOT / "dataset" / result.source.path).read_bytes()).hexdigest()
        assert result.source_sha256 == expected
        assert all(o.source_sha256 == expected for o in result.observations)


def test_public_labels_are_not_opened_by_ingestion(monkeypatch):
    original = structured_parser.read_records
    def guarded(path, *args, **kwargs):
        assert path.name not in {"sample_output.csv", "sample_deletion_requests.csv", "output.csv", "deletion_requests.csv"}
        return original(path, *args, **kwargs)
    monkeypatch.setattr(structured_parser, "read_records", guarded)
    assert not ingest_dataset(ROOT / "dataset").has_errors


def test_coverage_is_explicitly_parsing_not_semantic_accuracy(actual_bundle):
    report = coverage_metrics(actual_bundle)
    assert report["structured_files"] == report["fully_parsed_structured_files"] == 79
    assert report["deferred_files"] == 15
    assert report["structured_file_parse_rate"] == 1
    assert report["evidence_recall"] == report["deletion_accuracy"] == "NOT_MEASURED"
    assert actual_bundle.summary()["audit_complete"] is False


def test_csv_context_keeps_history_claims_and_non_citeable_snapshots(tmp_path):
    context_fixture(tmp_path)
    results = load_context_sources(tmp_path)
    assert all(r.status == ParseStatus.PARSED for r in results)
    identity, audit, activity, policy = (r.observations[0] for r in results)
    assert identity.evidence.citeable is False and identity.evidence.available_at is None
    assert policy.evidence.citeable is False and policy.observed_at is None
    assert audit.evidence.evidence_id == "synthetic_audit"
    assert {(i.kind, i.value) for i in audit.identifiers} >= {
        ("email", "old@example.invalid"), ("email", "new@example.invalid")}
    assert activity.claim_kind == "OPERATION_CLAIM"
    assert json.loads(activity.payload_json)["reported_result"] == "SUCCESS"


def test_one_failed_file_does_not_hide_other_sources(tmp_path):
    context_fixture(tmp_path)
    (tmp_path / "evidence").mkdir()
    (tmp_path / "evidence/good.json").write_text('{"records":[{"resource_id":"opaque","system":"svc"}]}', encoding="utf-8")
    write_csv(tmp_path / "evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"], [
        dict(file_id="good", file_path="evidence/good.json", origin="synthetic", captured_at="2026-01-01T00:00:00Z"),
        dict(file_id="missing", file_path="evidence/missing.log", origin="synthetic", captured_at="2026-01-01T00:00:00Z"),
    ])
    bundle = ingest_dataset(tmp_path)
    assert [r.status for r in bundle.files] == [ParseStatus.PARSED, ParseStatus.FAILED]
    assert bundle.has_errors
    assert bundle.index.lookup_resource("opaque").observations


def test_cross_source_evidence_id_collision_blocks_clean_coverage(tmp_path):
    context_fixture(tmp_path)
    (tmp_path / "evidence").mkdir()
    (tmp_path / "evidence/record.json").write_text('{"records":[]}', encoding="utf-8")
    write_csv(tmp_path / "evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"], [
        dict(file_id="synthetic_audit", file_path="evidence/record.json", origin="synthetic", captured_at="2026-01-01T00:00:00Z")])
    bundle = ingest_dataset(tmp_path)
    assert bundle.has_errors
    assert any(d.code == "EVIDENCE_ID_COLLISION" for d in bundle.diagnostics)


def test_empty_manifest_is_not_success(tmp_path):
    write_csv(tmp_path / "evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"], [])
    with pytest.raises(InputError): load_manifest(tmp_path)


def test_partial_context_counter_never_becomes_negative(tmp_path):
    context_fixture(tmp_path)
    path = tmp_path / "user_audit_log.csv"
    path.write_text(path.read_text(encoding="utf-8").replace("synthetic_audit", "").replace("2026-01-01T00:00:00Z", "bad"), encoding="utf-8")
    audit = load_context_sources(tmp_path)[1]
    assert audit.status == ParseStatus.PARTIAL
    assert audit.units_parsed == 0


def test_context_or_unknown_capture_cannot_be_used_as_a_citation(rows, context):
    source = context[2]["synthetic_evidence"]
    for changed, expected_code in [(replace(source, citeable=False), "CITATION_ROLE"),
                                   (replace(source, available_at=None), "CITATION_TIME")]:
        report = validate_rows(rows, context[0], {"synthetic_evidence": changed})
        assert expected_code in {i.code for i in report.issues}


def test_ingestion_cli_and_coverage_cli_account_for_all_sources():
    for relative, flag in [("code/main.py", "--ingest-evidence"),
                           ("code/evaluation/main.py", "--ingestion-coverage")]:
        process = subprocess.run([sys.executable, "-B", str(ROOT / relative), flag], capture_output=True, text=True)
        assert process.returncode == 0, process.stderr
        report = json.loads(process.stdout)
        assert report["manifest_files"] == 94
        assert report["has_ingestion_errors"] is False
    assert not (ROOT / "output.csv").exists()
