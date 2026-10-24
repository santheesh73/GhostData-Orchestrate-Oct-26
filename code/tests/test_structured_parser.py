from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

from ghosttrace.ingest.evidence_index import EvidenceIndex
from ghosttrace.ingest.csv_parser import parse_csv
from ghosttrace.ingest.json_parser import parse_json_document
from ghosttrace.ingest.log_parser import parse_log, parse_text
from ghosttrace.ingest.normalization import ParseStatus, strict_json
from ghosttrace.ingest.sql_parser import parse_sql
from ghosttrace.ingest.structured_parser import evidence_path, parse_source
from ghosttrace.models import EvidenceSource

TIME = datetime(2026, 1, 5, tzinfo=timezone.utc)
SOURCE = EvidenceSource("synthetic_file", TIME, "synthetic_origin", "evidence/synthetic.json")


def test_nested_snapshot_preserves_types_and_two_clocks():
    record = {"resource_id": "opaque", "email": "Old@Example.invalid", "phone": None,
              "enabled": False, "values": [], "profile": {}, "updated_at": "2020-01-01T00:00:00Z"}
    document = {"exported_at": TIME.isoformat(), "snapshots": [
        {"captured_at": "2026-01-01T00:00:00Z", "data_store": "synthetic_service",
         "collection": "synthetic_collection", "records": [record]}]}
    result = parse_json_document(json.dumps(document), SOURCE, "digest")
    observation = next(o for o in result.observations if o.resource.resource_id)
    assert result.status == ParseStatus.PARSED
    assert json.loads(observation.payload_json) == record
    assert json.loads(dict(observation.facts)["enabled"]) is False
    assert json.loads(dict(observation.facts)["phone"]) is None
    assert observation.observed_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert observation.evidence.available_at == TIME
    assert observation.location == "/snapshots/0/records/0"
    assert observation.source_sha256 == "digest"
    assert len(observation.observation_id) == 64


def test_nested_service_export_keeps_query_and_returned_document():
    document = {"exported_at": TIME.isoformat(), "service_exports": {"synthetic_search": {
        "queries": [{"observed_at": "2026-01-01T00:00:00Z", "resource_id": "query_resource",
                     "query": "old@example.invalid", "hits": {"total": 1, "documents": [
                         {"resource_id": "actual_resource", "email": "old@example.invalid"}]}}]}}}
    result = parse_json_document(json.dumps(document), SOURCE, "digest")
    assert result.status == ParseStatus.PARSED
    assert {o.resource.resource_id for o in result.observations if o.resource.resource_id} == {
        "query_resource", "actual_resource"}
    assert all(o.resource.system_id == "synthetic_search" for o in result.observations if o.resource.resource_id)


@pytest.mark.parametrize("text", ['{"records":[]}', '{"service_exports":{"svc":{"items":[]}}}'])
def test_empty_declared_collection_is_not_a_global_absence_proof(text):
    result = parse_json_document(text, SOURCE, "digest")
    assert result.status == ParseStatus.PARSED
    assert any(o.claim_kind == "SCOPE_METADATA" for o in result.observations)
    assert all(json.loads(o.payload_json).get("completeness") == "NOT_ESTABLISHED"
               for o in result.observations if o.claim_kind == "SCOPE_METADATA")


@pytest.mark.parametrize("text", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '[' * 80 + '0' + ']' * 80])
def test_strict_evidence_json_rejects_ambiguity(text):
    with pytest.raises(ValueError): strict_json(text)


def test_bad_record_is_explicitly_partial_without_losing_good_records():
    result = parse_json_document('{"records":[{"resource_id":"good"},42,{"email":"x@example.invalid"}]}', SOURCE, "digest")
    assert result.status == ParseStatus.PARTIAL
    assert {d.code for d in result.diagnostics} >= {"INVALID_RECORD", "MISSING_RESOURCE_ID"}
    assert any(o.resource.resource_id == "good" for o in result.observations)


def test_invalid_observation_time_does_not_fall_back_to_file_capture():
    result = parse_json_document('{"resource_id":"opaque","observed_at":"invalid"}', SOURCE, "digest")
    assert result.status == ParseStatus.PARTIAL
    assert result.observations[0].observed_at is None


@pytest.mark.parametrize("body", [
    'level=INFO service=svc trace_id=t event=read resource_id=r rows=0',
    '[INFO] [svc] [t] read: resource_id="r" rows="0"',
    '| INFO | svc | t | read | resource_id="r" rows="0"',
    '<15>1 node svc t - - level=INFO event="read" resource_id="r" rows="0"',
    '{"service":"svc","trace_id":"t","event":"read","resource_id":"r","rows":0}',
    'requestId=t level=INFO function=svc message="event=\\"read\\" resource_id=\\"r\\" rows=\\"0\\""',
])
def test_log_envelope_families(body):
    result = parse_log("2026-01-01T00:00:00Z " + body, SOURCE, "digest")
    assert result.status == ParseStatus.PARSED
    observation = result.observations[0]
    assert observation.resource.system_id == "svc"
    assert observation.resource.resource_id == "r"
    assert observation.trace_id == "t"
    assert observation.location == "line:1"
    assert json.loads(observation.payload_json)["raw_line"].endswith(body)


def test_trace_retrieval_links_events_without_merging_payloads():
    text = '\n'.join([
        '2026-01-01T00:00:00Z service=svc instance=a trace_id=t event=start lookup_key="person@example.invalid"',
        '2026-01-01T00:00:01Z service=svc instance=a trace_id=t event=read resource_id=opaque rows=0',
        '2026-01-01T00:00:02Z service=other instance=a trace_id=t event=read resource_id=decoy rows=1',
        '2026-01-01T00:00:03Z service=svc instance=b trace_id=t event=read resource_id=another rows=1',
    ])
    result = parse_log(text, SOURCE, "digest")
    index = EvidenceIndex(result.observations)
    matches = index.lookup_identifier("email", "PERSON@example.invalid")
    assert len(matches.observations) == 2
    assert {o.resource.resource_id for o in matches.observations} == {"", "opaque"}
    completed = next(o for o in matches.observations if o.resource.resource_id)
    assert "lookup_key" not in json.loads(completed.payload_json)
    assert not matches.supports_absence


def test_unknown_or_broken_log_lines_are_retained():
    result = parse_log('not an event\n2026-01-01T00:00:00Z {broken\n', SOURCE, "digest")
    assert result.status == ParseStatus.PARTIAL
    assert len(result.observations) == 2
    assert all(o.claim_kind == "RAW_UNPARSED" for o in result.observations)
    assert {d.code for d in result.diagnostics} >= {"UNPARSED_LOG_LINE", "INVALID_LOG_PAYLOAD"}


def test_text_record_and_unknown_narrative_accounting():
    text = 'Snapshot: 2026-01-01T00:00:00Z\n- 2026-01-01T00:00:00Z | svc | opaque | PROFILE | FOUND | old@example.invalid\nUnrecognized narrative'
    result = parse_text(text, SOURCE, "digest")
    assert result.status == ParseStatus.PARTIAL
    assert len(result.observations) == 2
    assert result.observations[0].resource.resource_id == "opaque"
    assert result.observations[1].claim_kind == "RAW_UNPARSED"


def test_sql_snapshot_supports_indexes_types_and_replica_separation():
    sql = '''-- Captured at: 2026-01-01T00:00:00Z
PRAGMA foreign_keys=on;
BEGIN TRANSACTION;
CREATE TABLE customer_data_primary(resource_id TEXT PRIMARY KEY,origin_system TEXT,collection_name TEXT,record_json TEXT);
CREATE TABLE customer_data_replica(resource_id TEXT PRIMARY KEY,origin_system TEXT,collection_name TEXT,record_json TEXT);
INSERT INTO customer_data_primary VALUES('opaque','svc','profiles','{"email":null,"enabled":false,"name":"a; b''s"}');
INSERT INTO customer_data_replica VALUES('opaque','svc','profiles','{"email":"old@example.invalid","enabled":true}');
CREATE INDEX idx_origin ON customer_data_primary(origin_system);
COMMIT;
-- snapshot_completed_at=2026-01-01T00:00:01Z
'''
    result = parse_sql(sql, SOURCE, "digest")
    records = [o for o in result.observations if o.resource.resource_id]
    assert result.status == ParseStatus.PARSED
    assert len(records) == 2
    assert {o.resource.physical_copy for o in records} == {"customer_data_primary", "customer_data_replica"}
    primary = next(o for o in records if o.resource.physical_copy.endswith("primary"))
    assert json.loads(primary.payload_json)["record"] == {"email": None, "enabled": False, "name": "a; b's"}
    assert primary.observed_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert primary.evidence.available_at == TIME
    assert len(EvidenceIndex(records).lookup_resource("opaque").observations) == 2


@pytest.mark.parametrize("sql", [
    "ATTACH DATABASE 'external.sqlite' AS extra;",
    "VACUUM INTO 'external.sqlite';",
    "PRAGMA writable_schema=ON;",
    "CREATE VIRTUAL TABLE x USING fts5(content);",
    "CREATE TABLE x(a); INSERT INTO x VALUES(load_extension('external'));",
    "CREATE TABLE x(a); CREATE TRIGGER t AFTER INSERT ON x BEGIN DELETE FROM x; END;",
    "CREATE TABLE x(a); INSERT INTO x SELECT randomblob(1000000);",
    "CREATE TABLE x(a)",
    "BEGIN; CREATE TABLE x(a); INSERT INTO x VALUES(1);",
])
def test_sql_rejects_non_dump_or_external_operations(sql, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises((ValueError, __import__('sqlite3').Error)):
        parse_sql(sql, SOURCE, "digest")
    assert not (tmp_path / "external.sqlite").exists()


@pytest.mark.parametrize("path", ["../outside.json", "evidence/../../outside.json", "/absolute.json",
                                   "C:\\outside.json", "C:outside.json", "sample_output.csv"])
def test_manifest_path_cannot_escape_evidence(tmp_path, path):
    with pytest.raises(ValueError): evidence_path(tmp_path, path)


def test_source_failure_and_document_deferral_are_explicit(tmp_path):
    folder = tmp_path / "evidence"
    folder.mkdir()
    (folder / "bad.json").write_text('{"resource_id":', encoding="utf-8")
    failed = parse_source(tmp_path, EvidenceSource("bad", TIME, "test", "evidence/bad.json"))
    assert failed.status == ParseStatus.FAILED
    assert failed.source_sha256
    (folder / "pending.pdf").write_bytes(b"%PDF-test")
    pending = parse_source(tmp_path, EvidenceSource("doc", TIME, "test", "evidence/pending.pdf"))
    assert pending.status == ParseStatus.DEFERRED
    assert pending.diagnostics[0].code == "DOCUMENT_EXTRACTION_DEFERRED"
    missing = parse_source(tmp_path, EvidenceSource("missing", TIME, "test", "evidence/missing.log"))
    assert missing.status == ParseStatus.FAILED


def test_csv_adapter_preserves_cells_and_reports_ragged_records():
    text = 'system,resource_id,email,enabled,observed_at\nsvc,opaque,,false,2026-01-01T00:00:00Z\nsvc,broken\n'
    result = parse_csv(text, SOURCE, "digest")
    assert result.status == ParseStatus.PARTIAL
    assert result.units_seen == 2 and result.units_parsed == 1
    payload = json.loads(result.observations[0].payload_json)
    assert payload["email"] == "" and payload["enabled"] == "false"
    assert result.observations[1].claim_kind == "RAW_UNPARSED"


def test_log_header_conflicts_are_preserved_and_diagnosed():
    text = '2026-01-01T00:00:00Z [INFO] [header_service] [t] read: service=payload_service resource_id=opaque'
    result = parse_log(text, SOURCE, "digest")
    assert result.status == ParseStatus.PARTIAL
    assert any(d.code == "ENVELOPE_CONFLICT" for d in result.diagnostics)
    payload = json.loads(result.observations[0].payload_json)
    assert payload["service"] == "payload_service"
    assert payload["header_fields"]["service"] == "header_service"


def test_empty_text_and_generic_csv_are_accounted_by_supported_format(tmp_path):
    folder = tmp_path / "evidence"
    folder.mkdir()
    (folder / "empty.txt").write_text("", encoding="utf-8")
    empty = parse_source(tmp_path, EvidenceSource("empty", TIME, "test", "evidence/empty.txt"))
    assert empty.status == ParseStatus.EMPTY and empty.format == "text"
    (folder / "rows.csv").write_text('resource_id,email\nopaque,p@example.invalid\n', encoding="utf-8")
    result = parse_source(tmp_path, EvidenceSource("csv", TIME, "test", "evidence/rows.csv"))
    assert result.status == ParseStatus.PARSED and result.format == "csv"


def test_bad_embedded_sql_json_is_not_an_ordinary_record_observation():
    sql = '''CREATE TABLE records(resource_id TEXT, origin_system TEXT, record_json TEXT);
INSERT INTO records VALUES('opaque','svc','{"email":"one@example.invalid","email":"two@example.invalid"}');'''
    result = parse_sql(sql, SOURCE, "digest")
    assert result.status == ParseStatus.PARTIAL
    record = next(o for o in result.observations if o.resource.resource_id)
    assert record.claim_kind == "RAW_UNPARSED"
    assert "record_json" in json.loads(record.payload_json)


def test_long_unbroken_log_text_is_bounded_and_retained():
    text = "2026-01-01T00:00:00Z service=svc event=read " + "a" * 100_000
    result = parse_log(text, SOURCE, "digest")
    assert result.status == ParseStatus.PARSED
    assert json.loads(result.observations[0].payload_json)["raw_line"] == text


def test_invalid_sql_resource_type_is_preserved_with_a_diagnostic():
    result = parse_sql("CREATE TABLE records(resource_id INTEGER);INSERT INTO records VALUES(123);", SOURCE, "digest")
    assert result.status == ParseStatus.PARTIAL
    assert any(d.code == "INVALID_RESOURCE_CONTEXT" for d in result.diagnostics)
    assert any(json.loads(o.payload_json).get("resource_id") == 123 for o in result.observations)
