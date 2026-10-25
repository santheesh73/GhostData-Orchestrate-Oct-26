"""Replay direct observations; operation outcomes remain claims in the timeline.

Presence is scoped to an explicit resource and physical copy. Empty inventory or
missing index hits without a resource never establish global absence. Booleans
are interpreted only for named fields, not by Python string truthiness.
"""

from collections import defaultdict
from dataclasses import replace

from ..ingest.normalization import canonical_json
from ..models import Uncertainty
from .conflict_resolver import resolve_facts
from .models import ResolvedFact, ResourceState, StateFact
from .signals import aware, eligible, payload

# SCHEMA adapters: exact business-event names observed in participant sources;
# no case IDs, output labels, or golden-answer patterns are involved.
READ_EVENTS = frozenset({"profile_lookup_completed", "contact_query_completed", "contact_lookup_completed",
    "index_query_completed", "record_lookup", "audit_record_read_completed", "support_ticket_read_completed",
    "analytics_profile_read_completed", "analytics_profile_read", "message_read", "connector_config_loaded",
    "connector_heartbeat", "connector_config_read_completed", "export_download_check_completed",
    "export_metadata_read_completed", "restore_policy_read_completed", "restore_candidate_evaluated",
    "restore_authorization_completed", "retained_order_loaded"})
SCAN_EVENTS = frozenset({"attachment_pii_scan", "message_pii_scan", "analytics_identity_scan"})
BOOL_FIELDS = frozenset({"enabled", "scheduler_registered", "restore_allowed", "archive_present", "available", "marker_found"})


def _boolean(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.casefold() in {"true", "false"}:
        return value.casefold() == "true"
    return None


def _count(value):
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        # Presence needs zero versus positive, not an unbounded integer parse.
        return 1 if value.lstrip("0") else 0
    return None


def extract_facts(observation):
    """Extraction is semantic observation only; it applies no deletion policy."""
    if not observation.resource.resource_id or not observation.resource.system_id or observation.observed_at is None:
        return ()
    kind, data = observation.claim_kind, payload(observation)
    if kind not in {"SQL_RECORD", "RECORD_SNAPSHOT", "LOG_EVENT"}:
        return ()
    if kind == "SQL_RECORD" and isinstance(data.get("record"), dict):
        data = data["record"]
    event = data.get("event", "")
    if kind == "LOG_EVENT" and event not in READ_EVENTS | SCAN_EVENTS | {"deletion_marker_check"}:
        return ()
    values = []
    def add(dimension, value):
        values.append(StateFact(observation.resource, dimension, canonical_json(value),
                                observation.observed_at, observation.observation_id))
    presence = []
    counts = [data.get(key) for key in ("rows", "total_hits") if key in data]
    hits = data.get("hits")
    if isinstance(hits, dict) and "total" in hits:
        counts.append(hits["total"])
    for value in counts:
        count = _count(value)
        if count is not None:
            presence.append("PRESENT" if count else "ABSENT")
    result = data.get("result")
    if isinstance(result, str) and result.upper() in {"FOUND", "HIT", "NOT_FOUND", "MISS", "ACTIVE", "DISABLED", "BLOCKED", "IDENTIFIABLE", "REDACTED", "ANONYMIZED"}:
        presence.append("ABSENT" if result.upper() in {"NOT_FOUND", "MISS"} else "PRESENT")
    if event == "profile_lookup_completed" and str(data.get("http_status")) == "404":
        presence.append("ABSENT")
    if str(data.get("status_code")) == "404" and "profile" in data and data["profile"] is None:
        presence.append("ABSENT")
    if event == "export_download_check_completed" and _boolean(data.get("available")) is True:
        presence.append("PRESENT")
    if event == "restore_candidate_evaluated" and _boolean(data.get("eligible")) is True:
        presence.append("PRESENT")
        add("/archive_present", True)
    category = data.get("record_type", observation.resource.category)
    sys_id = observation.resource.system_id
    res_id = observation.resource.resource_id or ""
    is_flow = category == "DATA_FLOW" or sys_id == "integration_service" or res_id.startswith("data_flow_")
    is_backup = category == "BACKUP_ARCHIVE" or sys_id == "backup_service" or res_id.startswith("backup_")
    if is_flow and result in {"ACTIVE", "DISABLED"}:
        add("/enabled", result == "ACTIVE")
    if is_backup and result in {"ACTIVE", "BLOCKED"}:
        add("/restore_allowed", result == "ACTIVE")
        add("/archive_present", True)
    if result in {"IDENTIFIABLE", "REDACTED", "ANONYMIZED"}:
        add("/identifier_treatment", result)
    if isinstance(hits, dict) and isinstance(hits.get("documents"), list) and hits["documents"]:
        presence.append("PRESENT")
    if not presence and kind in {"RECORD_SNAPSHOT", "SQL_RECORD"}:
        presence.append("PRESENT")
    if not presence and not counts and kind == "LOG_EVENT" and event in READ_EVENTS - {
            "restore_authorization_completed", "restore_candidate_evaluated", "export_download_check_completed"}:
        if any(key in data for key in BOOL_FIELDS | {"email", "customer_email", "requester_email", "subject_reference", "subject_ref", "message_text",
                                                    "customer_reference", "event_code", "retention_until", "access"}):
            presence.append("PRESENT")
    if event in SCAN_EVENTS and data.get("matched_value"):
        presence.append("PRESENT")
        add("scan_match", data["matched_value"])
    for state in sorted(set(presence)):
        add("presence", state)
    # Expose named process flags, not a risk verdict. The later policy engine
    # must decide how enabled/scheduler/archive/restore combinations apply.
    pending = [(data, "")]
    while pending:
        item, prefix = pending.pop()
        for key, value in sorted(item.items()):
            if key in {"raw_line", "record_json", "message", "header_fields", "message_fields", "extraction_proof"}:
                continue
            path = f"{prefix}/{key}"
            if isinstance(value, dict):
                pending.append((value, path))
            elif isinstance(value, list):
                if key == "documents":
                    for index, document in enumerate(value):
                        if isinstance(document, dict):
                            pending.append((document, f"{path}/{index}"))
            elif key in BOOL_FIELDS:
                boolean = _boolean(value)
                if boolean is not None:
                    add(path, boolean)
            elif (key.endswith("email_hash") or key.endswith("email") or key.endswith("phone")
                  or key in {"name", "full_name", "display_name", "requester_name", "customer_reference", "subject_reference", "subject_ref", "message_text", "user_id"}):
                add(path, value)
    if event in {"restore_authorization_completed", "restore_candidate_evaluated"}:
        if data.get("decision") in {"allow", "deny"}:
            add("/restore_allowed", data["decision"] == "allow")
            add("/archive_present", True)
            add("presence", "PRESENT")
    return tuple(values)


def replay(observations, cutoff):
    aware(cutoff)
    groups = defaultdict(list)
    for observation in observations:
        if eligible(observation, cutoff) == "ELIGIBLE" and observation.resource.resource_id:
            key = (observation.resource.system_id, observation.resource.resource_id, observation.resource.physical_copy)
            groups[key].append(observation)
    result = []
    direct_resources = {(o.resource.system_id, o.resource.resource_id) for group in groups.values()
                        for o in group if extract_facts(o)}
    for _, timeline in sorted(groups.items()):
        if (all(o.claim_kind == "OPERATION_CLAIM" for o in timeline)
                and (timeline[0].resource.system_id, timeline[0].resource.resource_id) in direct_resources):
            # A workflow/catalog row has no physical-copy identity. Preserve it
            # in reconstruction/link proofs, not as an extra empty data copy.
            continue
        timeline.sort(key=lambda o: (o.observed_at, o.observation_id))
        facts = resolve_facts(f for observation in timeline for f in extract_facts(observation))
        uncertainties = []
        if any(f.conflicting_values for f in facts):
            uncertainties.append(Uncertainty("CONFLICTING_STATE", "equal-time direct observations disagree"))
        if not facts:
            uncertainties.append(Uncertainty("STATE_NOT_ESTABLISHED", "resource has claims without a recognized direct state observation"))
        # Omission is not redaction. A later row snapshot, or an explicit later
        # absence readback, invalidates old field values as current-state proof.
        snapshots = [o for o in timeline if o.claim_kind in {"SQL_RECORD", "RECORD_SNAPSHOT"}]
        boundaries = [(o.observed_at, o.observation_id) for o in snapshots]
        boundaries.extend((f.observed_at, oid) for f in facts if f.dimension == "presence"
                          and f.value_json == '"ABSENT"' for oid in f.observation_ids)
        if boundaries:
            clock = max(t for t, _ in boundaries)
            proof = tuple(sorted({oid for t, oid in boundaries if t == clock}))
            stale = [f for f in facts if f.dimension.startswith("/") and f.observed_at < clock]
            if stale:
                stale_dimensions = {f.dimension for f in stale}
                facts = tuple(ResolvedFact(f.dimension, None, clock, proof)
                              if f.dimension in stale_dimensions else f for f in facts)
                uncertainties.append(Uncertainty("FIELD_NOT_OBSERVED_IN_LATEST_STATE",
                                                 "older fields are unknown after a later snapshot or absence readback"))
        categories = {o.resource.category for o in timeline if o.resource.category}
        resource = replace(timeline[-1].resource, category=next(iter(categories)) if len(categories) == 1 else "")
        if len(categories) > 1:
            uncertainties.append(Uncertainty("CATEGORY_CONFLICT", "source categories require later policy normalization"))
        result.append(ResourceState(resource, facts, tuple(timeline), tuple(uncertainties)))
    return tuple(result)
