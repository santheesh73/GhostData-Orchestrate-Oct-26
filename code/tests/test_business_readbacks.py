"""Counterfactual tests for literal business layouts and causal readbacks."""

import json

import pytest

from fixtures.history_cases import at, observation
from ghosttrace.ingest.log_parser import parse_log
from ghosttrace.models import EvidenceSource
from ghosttrace.policy.facts import project
from ghosttrace.policy.obligations import pii
from ghosttrace.resolve.temporal_replay import extract_facts
from test_phase06_repairs import document
from ghosttrace.extract.business import project_document


def data(rows):
    return {o.resource.resource_id: json.loads(o.payload_json) for o in rows}


def test_export_columns_bind_each_owner_without_catalog_or_id_suffix_inference():
    text = "Export ID\nopaque_713\nrandom_24\nFilename\nx.zip\ny.zip\nOwner\none@example.invalid\ntwo@example.invalid\nStatus\nReady"
    rows = data(project_document(document(text, "export_service"), {}))
    assert rows["opaque_713"]["owner_email"] == "one@example.invalid"
    assert rows["random_24"]["owner_email"] == "two@example.invalid"
    assert not project_document(document(text.replace("two@example.invalid\n", ""), "export_service"), {})
    assert not project_document(document(text.replace("random_24", "opaque_713"), "export_service"), {})


@pytest.mark.parametrize("origin,text,subjects,resource", [
    ("analytics_platform", "subject-Z opaque-document owner@example.invalid", {"subject-Z"}, "opaque-document"),
    ("search_index_admin", "Raw document • opaque-document\ncustomer_reference subject-Z", {"subject-Z"}, "opaque-document"),
    ("marketing_platform", "opaque-document owner@example.invalid\nLive profile fields updated", set(), "opaque-document"),
])
def test_explicit_headers_accept_opaque_ids(origin, text, subjects, resource):
    rows = project_document(document(text, origin), {}, subjects)
    assert [o.resource.resource_id for o in rows] == [resource]
    assert not project_document(document(text + "\nNo records", origin), {}, subjects)


def test_subject_headers_require_known_subject_and_reject_conflicting_bindings():
    text = "subject-Z opaque owner@example.invalid"
    assert not project_document(document(text, "analytics_platform"), {}, {"other-subject"})
    text += "\nsubject-Z opaque other@example.invalid"
    assert not project_document(document(text, "analytics_platform"), {}, {"subject-Z"})


@pytest.mark.parametrize("sync", ["Continuous Sync", "Continuous Sy nc"])
def test_live_connector_requires_unique_selected_identity_and_positive_deliveries(sync):
    text = f"opaque_519\nSelector\nowner@example.invalid\nSync mode\n{sync}\n124 events delivered"
    rows = data(project_document(document(text, "integration_admin"), {}))
    assert rows["opaque_519"]["enabled"] is True
    assert rows["opaque_519"]["subject_selector"] == "owner@example.invalid"
    for bad in (text.replace("124 events", "0 events"), text + "\nother@example.invalid", text + "\nother_28"):
        assert not project_document(document(bad, "integration_admin"), {})


def logs(lines, origin="support_platform"):
    source = EvidenceSource("literal-log", at(10), origin, "evidence/business.log")
    return parse_log("\n".join(lines), source, "literal-hash").observations


def event(name, minute=1, **fields):
    return f"2026-01-05T00:{minute:02d}:00Z " + json.dumps(dict(event=name, service="support_replica", trace_id="opaque-trace", instance="replica-A", **fields))


def test_query_metadata_is_timestamp_ordered_and_preserves_logical_owner():
    rows = logs([event("contact_query_completed", 2, resource_id="opaque"), event("contact_query_started", source="legacy_contact_index")])
    completed = rows[0]
    assert completed.resource.system_id == "support_platform"
    assert json.loads(completed.payload_json)["lookup_source"] == "legacy_contact_index"
    assert json.loads(completed.payload_json)["service"] == "support_replica"
    assert completed.resource.physical_copy == "replica-A"
    assert "lookup_source" not in json.loads(logs([event("contact_query_completed", 2)])[0].payload_json)


@pytest.mark.parametrize("changes", [
    {"minute": 3}, {"event": "different_query_started"}, {"service": "another-service"},
    {"instance": "replica-B"}, {"trace_id": "different-trace"},
])
def test_query_metadata_never_crosses_temporal_or_context_boundaries(changes):
    fields = dict(event="contact_query_started", minute=1, source="legacy_contact_index")
    fields.update(changes)
    name, minute = fields.pop("event"), fields.pop("minute")
    # Construct directly so overridden envelope fields remain explicit.
    start = dict(event=name, service="support_replica", trace_id="opaque-trace", instance="replica-A", **{})
    start.update(fields)
    rows = logs([f"2026-01-05T00:{minute:02d}:00Z " + json.dumps(start), event("contact_query_completed", 2)])
    assert "lookup_source" not in json.loads(rows[-1].payload_json)


def test_conflicting_query_starts_and_explicit_owner_never_get_overwritten():
    rows = logs([event("contact_query_started", source="legacy_contact_index"),
                 event("contact_query_started", source="other_index"), event("contact_query_completed", 2)])
    assert "lookup_source" not in json.loads(rows[-1].payload_json)
    rows = logs([event("contact_query_started", source="legacy_contact_index"),
                 event("contact_query_completed", 2, lookup_source="explicit")])
    assert json.loads(rows[-1].payload_json)["lookup_source"] == "explicit"
    assert logs([event("contact_query_completed", system="explicit_owner")])[0].resource.system_id == "explicit_owner"


@pytest.mark.parametrize("category,result,dimension,value", [
    ("DATA_FLOW", "ACTIVE", "/enabled", "true"),
    ("DATA_FLOW", "DISABLED", "/enabled", "false"),
    ("BACKUP_ARCHIVE", "BLOCKED", "/restore_allowed", "false"),
    ("SUPPORT_MESSAGE", "REDACTED", "/identifier_treatment", '"REDACTED"'),
])
def test_typed_record_lookups_are_state_evidence_but_workflow_results_are_not(category, result, dimension, value):
    fields = dict(event="record_lookup", record_type=category, result=result)
    assert any(f.dimension == dimension and f.value_json == value for f in extract_facts(observation("lookup", fields, kind="LOG_EVENT")))
    fields["event"] = "deletion_workflow_completed"
    assert not extract_facts(observation("workflow", fields, kind="LOG_EVENT"))


def summary_assessment(text, *, omit_phone=False, field="message_excerpt"):
    fields = dict(requester_name=None, requester_email=None, requester_phone=None, **{field: text})
    if omit_phone:
        fields.pop("requester_phone")
    # pii uses projected evidence fields, so exercise the real projection.
    from ghosttrace.resolve.temporal_replay import replay
    state = replay([observation("summary", fields)], at(20))[0]
    return pii(project(state), "SUPPORT_MESSAGE", (), "subject-Z")[0]


@pytest.mark.parametrize("text", ["Customer followed up about an order update.", "The customer asked support for delivery status.", "Customer inquired about account access."])
def test_generic_summaries_require_all_explicitly_cleared_identity_fields(text):
    assert summary_assessment(text) is False
    assert summary_assessment(text, omit_phone=True) is None
    assert summary_assessment(text, field="message_text") is None


@pytest.mark.parametrize("text", [
    "Customer asked about order 123.", "Customer Alice asked about delivery.",
    "Customer asked about order alice@example.invalid.", "Customer asked about account. Alice called.",
    "Customer asked about order update at Main Street.", "Customer asked about accountaccess.",
])
def test_arbitrary_or_identifying_prose_never_becomes_negative_pii_proof(text):
    assert summary_assessment(text) is None
