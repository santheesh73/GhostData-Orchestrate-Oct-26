"""Source-grounded recovery, multi-source policy and verification controls."""
from pathlib import Path
from dataclasses import replace

import pytest

from fixtures.history_cases import at, change, observation, request
from ghosttrace.ingest.evidence_index import EvidenceIndex
from ghosttrace.policy.engine import PolicyEngine
from ghosttrace.policy.rulebook import RuleBook
from ghosttrace.quality.audit_gate import check_audit
from ghosttrace.quality.audit_gate import derivation_errors
from ghosttrace.resolve.temporal_replay import extract_facts, replay
from ghosttrace.extract.catalog import catalog_documents
from ghosttrace.extract.business import project_document
from ghosttrace.ingest.normalization import make_observation
from ghosttrace.models import EvidenceSource
from ghosttrace.resolve.signals import eligible
from ghosttrace.ingest.loader import parse_timestamp
from test_phase06_repairs import document

ROOT = Path(__file__).resolve().parents[2]


def run(*records):
    engine = PolicyEngine(EvidenceIndex([change(), *records]), RuleBook.load(ROOT / "dataset"))
    result = engine.audit(request(), coverage_complete=True)
    return result, engine


@pytest.mark.parametrize("verb", ["includes", "contains"])
def test_literal_order_content_establishes_retained_context_without_clearing_pii(verb):
    result, engine = run(observation("message", {"record_type": "SUPPORT_MESSAGE", "subject_reference": "subject-A",
        "ticket_id": "opaque-ticket", "channel": "email", "message_text":
        f"Send the update to old@example.invalid. The affected order {verb}: Handcrafted vase."}))
    assert result.decision.status.value == "INCOMPLETE"
    assert [o.operation for o in result.decision.operations] == ["REPORT_EXPOSED_PII", "REDACT_RECORD", "VERIFY_RECORD_REDACTED"]
    assert not check_audit(result, engine.observations)


@pytest.mark.parametrize("text", ["Order status.", "No affected order includes: item.",
    'Example: "The affected order includes: item."', "The affected order includes: unknown.",
    'Example: "An illustrative conversation. The affected order includes: item."',
    "The affected order includes: ", "The affected order does not include any items."])
def test_keyword_empty_negated_or_quoted_order_mentions_are_not_context_proof(text):
    result, _ = run(observation("message", {"record_type": "SUPPORT_MESSAGE", "subject_reference": "subject-A",
        "message_text": text, "requester_email": "old@example.invalid"}))
    assert result.decision.status is None and not result.candidate_operations


@pytest.mark.parametrize("available,until,expected", [(8, "2030-01-01T00:00:00Z", True),
    (21, "2030-01-01T00:00:00Z", False), (8, "2025-01-01T00:00:00Z", False)])
def test_retention_interval_and_current_readback_may_have_separate_sources(available, until, expected):
    rule = observation("retention-source", {"record_type": "SECURITY_AUDIT_LOG", "subject_reference": "subject-A",
        "retention_until": until}, day=8, available=available)
    readback = observation("current-readback", {"event": "audit_record_read_completed", "record_type": "SECURITY_AUDIT_LOG",
        "subject_reference": "subject-A", "result": "FOUND"}, kind="LOG_EVENT", day=12)
    result, engine = run(rule, readback)
    if expected:
        assert result.decision.status.value == "COMPLETE"
        assert [(o.operation, o.evidence_id) for o in result.decision.operations] == [("VERIFY_RECORD_PRESENT", "current-readback")]
        assert not check_audit(result, engine.observations)
        assert len(result.assessments[0].observation_ids) == 2
    else:
        assert result.decision.status is None


def test_another_copy_cannot_lend_an_unscoped_retention_interval():
    dated = observation("dated", {"record_type": "SECURITY_AUDIT_LOG", "subject_reference": "subject-A", "retention_until": "2030-01-01T00:00:00Z"}, copy="primary")
    undated = observation("undated", {"record_type": "SECURITY_AUDIT_LOG", "subject_reference": "subject-A"}, copy="separate")
    result, _ = run(dated, undated)
    assert result.decision.status is None


def test_typed_restore_eligibility_is_direct_permission_but_not_archive_existence():
    readback = observation("permission", {"event": "restore_candidate_evaluated", "eligible": True, "deletion_block": False}, kind="LOG_EVENT")
    facts = extract_facts(readback)
    assert {f.dimension for f in facts} >= {"/eligible", "/deletion_block"}
    assert not any(f.dimension in {"presence", "/archive_present"} for f in facts)
    claim = observation("claim", {"event_type": "CHECK_RESTORE_ACCESS"}, kind="OPERATION_CLAIM", copy="")
    assert len(replay([claim, readback], at(20))) == 1


@pytest.mark.parametrize("category,fields,verification", [
    ("USER_PROFILE", {"result": "NOT_FOUND"}, "VERIFY_RECORD_ABSENT"),
    ("SECURITY_AUDIT_LOG", {"retention_until": "2030-01-01T00:00:00Z"}, "VERIFY_RECORD_PRESENT"),
    ("ANALYTICS_PROFILE", {"email": None, "phone": None, "email_hash": None, "subject_reference": None}, "VERIFY_RECORD_ANONYMIZED"),
    ("ACCOUNT_TOMBSTONE", {"account_status": "deleted", "name": None, "email": None, "phone": None, "email_hash": None}, "VERIFY_RECORD_REDACTED"),
    ("DATA_FLOW", {"enabled": False}, "VERIFY_DATA_FLOW_DISABLED"),
    ("BACKUP_ARCHIVE", {"archive_present": True, "restore_allowed": False}, "VERIFY_RESTORE_BLOCKED"),
])
def test_already_compliant_obligation_is_verified_alongside_another_violation(category, fields, verification):
    before = observation("earlier-owner", {"record_type": category, "subject_reference": "subject-A"}, resource="compliant", day=8)
    compliant = observation("current", {"record_type": category, "subject_reference": "subject-A", **fields}, resource="compliant", day=10)
    violation = observation("remaining", {"record_type": "SEARCH_INDEX_ENTRY", "subject_reference": "subject-A"}, resource="remaining")
    result, engine = run(before, compliant, violation)
    assert result.decision.status.value == "INCOMPLETE"
    assert verification in [o.operation for o in result.decision.operations if o.resource_id == "compliant"]
    assert all(o.evidence_id == "" for o in result.decision.operations if o.operation.startswith("VERIFY_"))
    assert not check_audit(result, engine.observations)


def catalog(resource="opaque-object", label="agreement.pdf", day=12, system="object_storage", user="subject-A"):
    source = EvidenceSource("catalog-" + resource, at(day), "context_csv", "system_activity.csv")
    details = f"Attachment catalog confirmed {resource} ({label}) belongs only to old@example.invalid and {user}; no other subject is linked."
    return make_observation(source, "catalog-hash", "line:2", {"event_type": "LINK_RESOURCE_IDENTITY", "resource_id": resource,
        "details": details, "catalog_filename": label, "catalog_subject_reference": user, "catalog_sole_subject": True},
        system=system, resource=resource, observed_at=at(day), claim_kind="OPERATION_CLAIM")


def test_literal_catalog_filename_mapping_recovers_object_without_id_similarity():
    source = document("Nimbus Object Storage\nObjects\nagreement.pdf", "object_storage")
    binding = catalog(resource="urn:arbitrary:object")
    rows = catalog_documents(source, [binding])
    assert len(rows) == 1 and rows[0].resource.resource_id == "urn:arbitrary:object"
    assert rows[0].observed_at == at(10) and rows[0].derived_available_at == at(12)
    assert eligible(rows[0], at(11)) == "FUTURE"
    assert not EvidenceIndex(rows).lookup_resource("urn:arbitrary:object", at=at(11)).observations
    assert eligible(rows[0], at(20)) == "ELIGIBLE"
    result, engine = run(binding, rows[0], *source.observations)
    assert result.decision.status.value == "INCOMPLETE"
    assert [o.operation for o in result.decision.operations] == ["REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT"]
    assert not check_audit(result, engine.observations)


def test_catalog_claim_or_filename_alone_still_cannot_prove_object_state():
    source = document("Nimbus Object Storage\nObjects\nother.pdf", "object_storage")
    binding = catalog()
    assert not catalog_documents(source, [binding])
    result, _ = run(binding)
    assert result.decision.status is None


def test_future_alias_collision_does_not_rewrite_an_earlier_valid_join():
    source = document("Nimbus Object Storage\nagreement.pdf", "object_storage")
    rows = catalog_documents(source, [catalog(), catalog(resource="other-object", day=21)])
    assert len(rows) == 1
    assert eligible(rows[0], at(20)) == "ELIGIBLE"
    assert eligible(rows[0], at(21)) == "AMBIGUOUS_DERIVATION"
    assert not EvidenceIndex(rows).lookup_resource(rows[0].resource.resource_id, at=at(21)).observations
    assert not catalog_documents(source, [catalog(), catalog(resource="other-object")])


def test_wrong_system_or_partial_filename_cannot_bind_a_catalog_resource():
    source = document("Nimbus Object Storage\nnot-agreement.pdf", "object_storage")
    assert not catalog_documents(source, [catalog()])
    assert not catalog_documents(document("agreement.pdf", "object_storage"), [catalog(system="other")])


def test_independent_gate_rejects_missing_or_backdated_join_proof():
    doc = document("Nimbus Object Storage\nagreement.pdf", "object_storage")
    binding = catalog()
    row, = catalog_documents(doc, [binding])
    index = {o.observation_id: o for o in (binding, row, *doc.observations)}
    assert not derivation_errors(row, index, at(20))
    assert derivation_errors(row, {}, at(20)) == ("DERIVED_BINDING_PROOF",)
    assert derivation_errors(replace(row, derived_available_at=at(10)), index, at(20)) == ("DERIVED_BINDING_TIME",)


def test_selected_conversation_can_supply_a_literal_order_reference():
    text = "Helpline Console\nsupport_82\nConversation\nSender\nAssigned agent\nowner@example.invalid\norder purchase:opaque"
    import json
    rows = project_document(document(text, "support_platform"), {})
    assert len(rows) == 1
    assert json.loads(rows[0].payload_json)["order_reference"] == "purchase:opaque"
    assert all("order_reference" not in json.loads(o.payload_json) for o in project_document(document(text + "\norder other:opaque", "support_platform"), {}))


@pytest.mark.parametrize("variation", ["reorder", "duplicate", "unrelated", "opaque_rename", "equivalent_time"])
def test_recovery_semantics_survive_irrelevant_input_changes(variation):
    good = observation("good", {"record_type": "USER_PROFILE", "subject_reference": "subject-A", "result": "NOT_FOUND"}, resource="first")
    bad = observation("bad", {"record_type": "SEARCH_INDEX_ENTRY", "subject_reference": "subject-A"}, resource="second")
    baseline, _ = run(good, bad)
    records = [good, bad]
    if variation == "reorder": records.reverse()
    elif variation == "duplicate": records += records[:]
    elif variation == "unrelated": records.append(observation("other", {"record_type": "USER_PROFILE", "user_id": "other-subject"}, resource="unrelated"))
    elif variation == "opaque_rename": records = [replace(o, resource=replace(o.resource, resource_id={"first": "urn:opaque:alpha", "second": "random/document"}[o.resource.resource_id])) for o in records]
    else: records = [replace(o, observed_at=parse_timestamp(o.observed_at.isoformat().replace("+00:00", "Z"), "equivalent")) for o in records]
    actual, engine = run(*records)
    assert actual.decision.status == baseline.decision.status
    assert [o.operation for o in actual.decision.operations] == [o.operation for o in baseline.decision.operations]
    assert not check_audit(actual, engine.observations)


@pytest.mark.parametrize("text", ["The affected order includes: Ceramic mug.", "the affected order contains :   Ceramic mug.", "The affected order includes:\nCeramic mug."])
def test_order_context_supports_safe_formatting_without_changing_the_pii_obligation(text):
    result, _ = run(observation("format", {"record_type": "SUPPORT_MESSAGE", "subject_reference": "subject-A", "message_text": text, "requester_email": "old@example.invalid"}))
    assert result.decision.status.value == "INCOMPLETE"
    assert "REDACT_RECORD" in [o.operation for o in result.decision.operations]


def test_continued_attachment_properties_bind_the_literal_reference_without_sole_ownership():
    import json
    text = "DELIVERY ADDRESS CORRECTION REQUEST\nSupport reference CS-opaque / urn:form\nowner@example.invalid\nContinued - Attachment properties and upload history\nfile signed-request.pdf\nuploader customer"
    rows = project_document(document(text, "support_platform"), {})
    assert len(rows) == 1 and rows[0].resource.resource_id == "urn:form"
    assert json.loads(rows[0].payload_json)["record_type"] == "SUPPORT_ATTACHMENT"
    assert "sole_subject" not in json.loads(rows[0].payload_json)
    assert not project_document(document(text.replace("Attachment properties and upload history", "Customer notes")), {})
    assert not project_document(document(text + "\nother@example.invalid"), {})


@pytest.mark.parametrize("observed_day,verify", [(2, False), (5, True), (9, True)])
def test_prediction_verifies_absence_only_from_request_time_onward(observed_day, verify):
    old_or_current = observation("negative-read", {"event": "profile_lookup_completed", "rows": 0,
        "http_status": 404, "subject_reference": "subject-A"}, day=observed_day,
        system="account_service", resource="opaque-profile", kind="LOG_EVENT")
    remaining = observation("remaining-now", {"record_type": "SEARCH_INDEX_ENTRY", "subject_reference": "subject-A"},
        system="search_service", resource="opaque-search")
    engine = PolicyEngine(EvidenceIndex([change(day=0), old_or_current, remaining]),
        RuleBook.load(ROOT / "dataset"), prediction_defaults=True)
    result = engine.audit(request(), coverage_complete=True)
    assert result.decision.status.value == "INCOMPLETE"
    checks = [op for op in result.decision.operations if op.resource_id == "opaque-profile"]
    assert bool(checks) is verify
    assert all(op.operation == "VERIFY_RECORD_ABSENT" and op.evidence_id == "" for op in checks)


def test_prediction_keeps_present_profile_observed_before_request():
    present = observation("present-read", {"record_type": "USER_PROFILE", "subject_reference": "subject-A"},
        day=2, system="account_service", resource="opaque-profile")
    engine = PolicyEngine(EvidenceIndex([change(day=0), present]),
        RuleBook.load(ROOT / "dataset"), prediction_defaults=True)
    result = engine.audit(request(), coverage_complete=True)
    assert result.decision.status.value == "INCOMPLETE"
    assert [op.operation for op in result.decision.operations] == [
        "REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT"]
