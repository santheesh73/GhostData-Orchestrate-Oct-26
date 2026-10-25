"""Independent adversarial controls for the final recovery contract."""
import json
from pathlib import Path

import pytest

from fixtures.history_cases import at, change, observation, request
from ghosttrace.extract.business import project_document
from ghosttrace.ingest.evidence_index import EvidenceIndex
from ghosttrace.policy.engine import PolicyEngine
from ghosttrace.policy.rulebook import RuleBook
from ghosttrace.resolve.temporal_replay import extract_facts
from test_phase06_repairs import document

ROOT = Path(__file__).resolve().parents[2]


def audit(category, fields):
    o = observation("literal-proof", {"record_type": category, "subject_reference": "subject-A", **fields})
    engine = PolicyEngine(EvidenceIndex([change(), o]), RuleBook.load(ROOT / "dataset"))
    return engine.audit(request(), coverage_complete=True)


@pytest.mark.parametrize("category,fields", [
    ("SUPPORT_ATTACHMENT", {"email": "old@example.invalid"}),
    ("SUPPORT_ATTACHMENT", {}),
    ("SECURITY_AUDIT_LOG", {}),
    ("SECURITY_AUDIT_LOG", {"integrity_seal": "signed"}),
    ("SECURITY_AUDIT_LOG", {"retention_until": "malformed"}),
    ("SECURITY_AUDIT_LOG", {"retention_until": "2030-01-01T00:00:00Z", "retention_from": "malformed"}),
    ("LEGAL_HOLD_RECORD", {}),
    ("SUPPORT_MESSAGE", {"requester_email": "old@example.invalid"}),
    ("BACKUP_ARCHIVE", {"archive_present": True}),
    ("ACCOUNT_TOMBSTONE", {"account_status": "inactive", "email": None, "phone": None, "name": None, "email_hash": None}),
])
def test_missing_conditions_never_become_compliance_or_destructive_permission(category, fields):
    result = audit(category, fields)
    assert result.decision.status is None
    assert not result.candidate_operations


@pytest.mark.parametrize("field", ["message_excerpt", "message_text", "body", "notes"])
def test_unknown_residual_text_is_not_a_redaction_certificate(field):
    result = audit("SUPPORT_MESSAGE", {"shared_context": True, "requester_name": None,
        "requester_email": None, "requester_phone": None, "nested": {field: "Deliver to 48 River Road."}})
    assert result.decision.status is None


@pytest.mark.parametrize("category,fields,operation", [
    ("SUPPORT_ATTACHMENT", {"sole_subject": True}, "DELETE_RECORD"),
    ("SUPPORT_MESSAGE", {"shared_context": True, "requester_email": "old@example.invalid"}, "REDACT_RECORD"),
    ("SECURITY_AUDIT_LOG", {"retention_until": "2030-01-01T00:00:00Z"}, "VERIFY_RECORD_PRESENT"),
    ("LEGAL_HOLD_RECORD", {"hold_active": True}, "VERIFY_RECORD_PRESENT"),
    ("BACKUP_ARCHIVE", {"archive_present": True, "restore_allowed": False}, "VERIFY_RESTORE_BLOCKED"),
])
def test_explicit_positive_policy_facts_still_work(category, fields, operation):
    result = audit(category, fields)
    assert result.decision.status is not None
    assert operation in [o.operation for o in result.decision.operations]


@pytest.mark.parametrize("origin,text", [
    ("identity_service", "Production workspace\nuser_913"),
    ("account_history_service", "Customer statement NST-2026-19-842"),
    ("object_storage", "Nimbus Object Storage\ndelivery_confirmation_842.pdf"),
])
def test_no_numeric_suffix_resource_invention(origin, text):
    assert project_document(document(text, origin), {}) == ()


@pytest.mark.parametrize("origin,text,resource", [
    ("identity_service", "Customer reference\ntombstone_27\nuser_913", "tombstone_27"),
    ("integration_admin", "BridgeOps\ndata_flow_43\nDisconnected\nUnrelated component Active", "data_flow_43"),
    ("object_storage", "Nimbus Object Storage\nobject_74\nowner@example.invalid", "object_74"),
])
def test_literal_resource_presence_never_invents_policy_fields(origin, text, resource):
    for row in project_document(document(text, origin), {}):
        data = json.loads(row.payload_json)
        assert data["resource_id"] == resource
        assert not {"account_status", "name", "phone", "email_hash", "sole_subject", "enabled", "scheduler_registered"} & data.keys()


def test_uploader_form_is_not_exclusive_subject_proof():
    text = "DELIVERY ADDRESS CORRECTION REQUEST\nSupport reference ticket / literal-object\nuploader customer\nowner@example.invalid"
    rows = project_document(document(text), {})
    assert all(json.loads(row.payload_json).get("sole_subject") is not True for row in rows)


def test_explicit_labeled_deleted_record_preserves_literal_nulls_without_guesses():
    text = "Resource ID: opaque-record\naccount_status: deleted\nuser_id: subject-A\nname: null\nemail: null\nphone: null\nemail_hash: null"
    rows = project_document(document(text, "identity_service"), {})
    assert len(rows) == 1
    data = json.loads(rows[0].payload_json)
    assert data["resource_id"] == "opaque-record" and data["account_status"] == "deleted"
    assert all(data[k] is None for k in ("name", "email", "phone", "email_hash"))


@pytest.mark.parametrize("decision", ["allow", "deny"])
def test_restore_decision_is_not_archive_presence(decision):
    fields = {"event": "restore_authorization_completed", "decision": decision}
    facts = extract_facts(observation("authorization", fields, kind="LOG_EVENT"))
    assert any(f.dimension == "/restore_allowed" for f in facts)
    assert not any(f.dimension in {"presence", "/archive_present"} for f in facts)


def test_identifier_spelling_does_not_supply_a_policy_category():
    result = audit("", {"resource_id": "support_24"})
    assert result.decision.status is None
    # The fixture resource is opaque too; exercise the prefix explicitly.
    row = observation("prefix", {"subject_reference": "subject-A"}, resource="support_24")
    engine = PolicyEngine(EvidenceIndex([change(), row]), RuleBook.load(ROOT / "dataset"))
    result = engine.audit(request(), coverage_complete=True)
    assert "UNMAPPED_POLICY_CATEGORY" in {u.code for a in result.assessments for u in a.uncertainties}


def test_explicitly_identified_storage_object_uses_only_literal_fields():
    text = "Resource ID: opaque-object\nemail: owner@example.invalid\nsole_subject: true"
    rows = project_document(document(text, "object_storage"), {})
    assert len(rows) == 1
    assert rows[0].resource.resource_id == "opaque-object"
    assert json.loads(rows[0].payload_json)["sole_subject"] is True


@pytest.mark.parametrize("category,fields", [
    ("SUPPORT_ATTACHMENT", {"sole_subject": False}),
    ("SECURITY_AUDIT_LOG", {"retention_until": "2025-01-01T00:00:00Z"}),
    ("LEGAL_HOLD_RECORD", {"hold_active": False}),
    ("BACKUP_ARCHIVE", {"eligible": True, "deletion_block": False}),
])
def test_false_or_incomplete_conditions_never_invent_an_alternative_delete_policy(category, fields):
    result = audit(category, fields)
    assert result.decision.status is None and not result.candidate_operations


@pytest.mark.parametrize("category,key", [("SUPPORT_ATTACHMENT", "sole_subject"), ("SUPPORT_MESSAGE", "shared_context"), ("LEGAL_HOLD_RECORD", "hold_active")])
def test_conflicting_same_time_conditions_remain_unknown(category, key):
    records = [observation(str(value), {"record_type": category, "subject_reference": "subject-A", key: value}) for value in (True, False)]
    engine = PolicyEngine(EvidenceIndex([change(), *records]), RuleBook.load(ROOT / "dataset"))
    result = engine.audit(request(), coverage_complete=True)
    assert result.decision.status is None and not result.candidate_operations


def test_multisubject_attachment_cannot_be_deleted_despite_exclusive_flag():
    row = observation("multiple", {"record_type": "SUPPORT_ATTACHMENT", "subject_reference": "subject-A", "owner_user_id": "subject-B", "sole_subject": True})
    other = change("other", user="subject-B", old="other@example.invalid", new="second@example.invalid")
    engine = PolicyEngine(EvidenceIndex([change(), other, row]), RuleBook.load(ROOT / "dataset"))
    result = engine.audit(request(), coverage_complete=True)
    assert result.decision.status is None
    assert not result.candidate_operations


@pytest.mark.parametrize("text", ["The customer inquired about delivery schedule.", "Customer requested support for order status.", "Customer asked support about delivery details."])
def test_explicit_generic_order_or_agent_context_can_be_interpreted(text):
    result = audit("SUPPORT_MESSAGE", {"requester_name": None, "requester_email": None,
                                     "requester_phone": None, "message_excerpt": text})
    assert result.decision.status is not None
    assert [o.operation for o in result.decision.operations] == ["VERIFY_RECORD_REDACTED"]


def test_generic_summary_does_not_clear_a_concrete_detail_or_unrelated_account_text():
    for text in ("Customer requested account access.", "Customer asked support about order 948."):
        result = audit("SUPPORT_MESSAGE", {"requester_name": None, "requester_email": None,
                                         "requester_phone": None, "message_excerpt": text})
        assert result.decision.status is None
