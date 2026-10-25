"""Three-valued policy evaluation. Missing conditions never authorize DELETE."""

from dataclasses import replace
import json
import re

from ..ingest.loader import InputError, parse_timestamp
from ..models import OperationDerivation, Uncertainty
from .facts import DIRECT_FIELDS, REFERENCE_FIELDS, TEXT_FIELDS, direct_key, field_key, named, project
from .models import Assessment


def decoded(fact):
    return json.loads(fact.value_json) if fact is not None and fact.value_json is not None else ...


def flag(facts, *names):
    candidates = named(facts, *names)
    values = {f.value_json for f in candidates}
    if not candidates or None in values or len(values) != 1:
        return None, candidates
    value = decoded(candidates[0])
    return (value if type(value) is bool else None), candidates


def generic_support_summary(value):
    """Interpret a complete finite language of non-identifying support summaries.

    This is not a failed-PII-scan fallback: every token and the subject/verb/topic
    structure must be understood. Unrecognized prose remains UNKNOWN.
    """
    if not isinstance(value, str) or len(value) > 256:
        return False
    words = value.casefold().removesuffix(".").split()
    if words[:1] == ["the"]:
        words = words[1:]
    vocabulary = {"the", "customer", "contacted", "asked", "inquired", "requested", "followed", "up", "support", "about", "for", "a", "an", "on", "account", "access", "order", "update", "delivery", "schedule", "status", "request", "to", "correct", "details", "supplied", "contact", "query"}
    return (len(words) >= 4 and words[0] == "customer" and words[1] in {"contacted", "asked", "inquired", "requested", "followed", "supplied"}
            and set(words) <= vocabulary and bool(set(words) & {"account", "order", "delivery"}))


def condition(rule, facts, user, audit_at):
    text = rule.condition
    if text == "Always":
        return True, ()
    if text == "Conversation contains shared customer, agent, or order context that must be retained":
        explicit, proof = flag(facts, "shared_context")
        if explicit is not None or proof:
            return explicit, proof
        # Explicit participant/order fields establish the retained context;
        # record presence or a treatment/status flag alone cannot do so.
        context = named(facts, "agent_email", "agent_name", "order_reference")
        supported = tuple(f for f in context if isinstance(decoded(f), str) and decoded(f).strip())
        if supported:
            return True, supported
        # A source-labeled declarative order-content section establishes order
        # context, even when another sentence exposes PII. This does not certify
        # the text clean and does not treat an arbitrary keyword as a condition.
        for fact in named(facts, "message_text", "message_excerpt"):
            value = decoded(fact)
            if not isinstance(value, str):
                continue
            match = re.search(r"(?:^|[.!?]\s+)(?:the\s+)?affected\s+order\s+(?:includes|contains)\s*:\s*([^.!?\n]+)", value, re.I)
            prefix = value[:match.start()] if match else ""
            if prefix.count('"') % 2 or prefix.count("`") % 2 or prefix.count("“") > prefix.count("”"):
                continue
            if match and match[1].strip() and not re.match(r"(?:unknown|null|none|n/a|not|no)\b", match[1].strip(), re.I):
                return True, (fact,)
        summaries = tuple(f for f in named(facts, "message_excerpt", "message_text")
                          if generic_support_summary(decoded(f)) and re.search(r"\b(?:support|order|delivery)\b", decoded(f), re.I))
        if summaries:
            return True, summaries
        return None, ()
    if text == "Attachment belongs only to the deletion subject":
        return flag(facts, "sole_subject")
    if text == "Record is still attributable to a user":
        fields = named(facts, *(DIRECT_FIELDS | REFERENCE_FIELDS)) + tuple(f for f in facts if f.dimension == "scan_match")
        if any(isinstance(decoded(f), str) and decoded(f).strip() for f in fields):
            return True, fields
        if fields and all(decoded(f) in (None, "") for f in fields):
            return False, fields
        return None, fields
    if text == "Log contains a user email address":
        fields = named(facts, "email", "customer_email", "requester_email", "owner_email")
        if any(isinstance(decoded(f), str) and decoded(f).strip() for f in fields):
            return True, fields
        return (False if fields and all(decoded(f) in (None, "") for f in fields) else None), fields
    if text == "Record is within the supplied retention period":
        fields = named(facts, "retention_until", "retention_from")
        until = named(facts, "retention_until")
        try:
            if len(until) != 1 or not isinstance(decoded(until[0]), str):
                return None, fields
            start = named(facts, "retention_from")
            if start and (len(start) != 1 or not isinstance(decoded(start[0]), str)):
                return None, fields
            begins = parse_timestamp(decoded(start[0]), "retention_from") if start else None
            return ((begins is None or begins <= audit_at) and audit_at < parse_timestamp(decoded(until[0]), "retention_until")), fields
        except (InputError, TypeError):
            return None, fields
    if text == "A supplied legal hold is active":
        explicit, proof = flag(facts, "hold_active", "legal_hold_active")
        if explicit is not None or proof:
            return explicit, proof
        until, reason = named(facts, "retained_until"), named(facts, "retention_reason")
        if len(until) == 1 and len(reason) == 1 and isinstance(decoded(reason[0]), str) and decoded(reason[0]):
            try:
                return audit_at < parse_timestamp(decoded(until[0]), "retained_until"), until + reason
            except InputError:
                pass
        return None, until + reason
    if text == "Restore access can be blocked":
        supported, proof = flag(facts, "restore_block_supported")
        if supported is not None or proof:
            return supported, proof
        allowed, proof = flag(facts, "restore_allowed")
        if allowed is None:
            possible, possible_proof = flag(facts, "eligible")
            block, block_proof = flag(facts, "deletion_block")
            if possible is not None and block is not None:
                return True, possible_proof + block_proof
        return (True if allowed is not None else None), proof
    if text == "Account is deleted and only a stable internal user_id is needed to preserve references to retained records":
        fields = named(facts, "account_status")
        refs = named(facts, *REFERENCE_FIELDS)
        if len(fields) == 1 and isinstance(decoded(fields[0]), str) and decoded(fields[0]).casefold() == "deleted" and any(decoded(f) == user for f in refs):
            return True, fields + refs
        return None, fields + refs
    return None, ()


def pii(facts, category, aliases, user):
    """Positive exposure needs one observed value; negative proof needs all
    required field kinds explicitly cleared. Unstructured negative recall defers.
    """
    fields = tuple(f for f in facts if direct_key(field_key(f.dimension)) and
                   (category == "ACCOUNT_TOMBSTONE" or not field_key(f.dimension).startswith(("agent_", "staff_"))))
    if category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"}:
        fields += named(facts, *REFERENCE_FIELDS)
    else:
        fields += tuple(f for f in named(facts, *REFERENCE_FIELDS)
                        if isinstance(decoded(f), str) and decoded(f).strip() and decoded(f) != user)
    positive = [f for f in fields if isinstance(decoded(f), str) and decoded(f).strip()]
    texts = named(facts, *TEXT_FIELDS)
    for fact in texts:
        value = decoded(fact)
        if isinstance(value, str) and any(alias.value and re.search(r"(?<!\w)" + re.escape(alias.value) + r"(?!\w)", value, re.IGNORECASE)
                                          for alias in aliases if alias.kind in {"email", "email_hash", "phone"}):
            positive.append(fact)
    scans = tuple(f for f in facts if f.dimension == "scan_match" and isinstance(decoded(f), str)
                  and any(decoded(f).casefold() == alias.value.casefold() for alias in aliases))
    positive.extend(scans)
    if positive:
        return True, tuple(positive)
    treatments = named(facts, "identifier_treatment")
    if len(treatments) == 1 and decoded(treatments[0]) in {"IDENTIFIABLE", "REDACTED", "ANONYMIZED"}:
        return decoded(treatments[0]) == "IDENTIFIABLE", treatments
    if category == "SUPPORT_MESSAGE" and texts and all(
            isinstance(decoded(f), str) and re.fullmatch(r"\[(?:REDACTED|REMOVED)\]", decoded(f), re.I) for f in texts):
        return False, texts
    present = set()
    for fact in fields:
        if decoded(fact) not in (None, ""):
            return None, fields
        key = field_key(fact.dimension)
        if key in REFERENCE_FIELDS:
            present.add("reference")
        elif "email_hash" in key:
            present.add("email_hash")
        elif "email" in key:
            present.add("email")
        elif "phone" in key:
            present.add("phone")
        elif "name" in key:
            present.add("name")
    required = {"email"} if category == "EMAIL_DELIVERY_LOG" else {"name", "email", "phone", "email_hash"} if category == "ACCOUNT_TOMBSTONE" else {"email", "phone", "email_hash", "reference"} if category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"} else {"name", "email", "phone"}
    def generic_summary(fact):
        return (category == "SUPPORT_MESSAGE" and field_key(fact.dimension) == "message_excerpt"
                and generic_support_summary(decoded(fact)))
    if not required <= present or any(decoded(f) not in (None, "") and not generic_summary(f) for f in texts):
        return None, fields + texts
    return False, fields + texts


def assess(state, book, user, aliases, audit_at, observations, context_observations=()):
    facts = project(state)
    payloads = {o.observation_id: json.loads(o.payload_json) for o in state.timeline}
    category = book.category(state, payloads)
    if category == "SUPPORT_ATTACHMENT":
        # Explicit catalog ownership is a condition proof, never a presence
        # readback. It can corroborate an independently observed stored object.
        from ..resolve.models import ResolvedFact
        from ..resolve.signals import eligible
        for o in context_observations:
            data = json.loads(o.payload_json)
            if (o.claim_kind == "OPERATION_CLAIM" and o.evidence.path == "system_activity.csv"
                    and eligible(o, audit_at) == "ELIGIBLE"
                    and (o.resource.system_id, o.resource.resource_id) == (state.resource.system_id, state.resource.resource_id)
                    and data.get("event_type") == "LINK_RESOURCE_IDENTITY"
                    and data.get("catalog_sole_subject") is True
                    and data.get("catalog_subject_reference") == user):
                facts += (ResolvedFact("/sole_subject", "true", o.observed_at, (o.observation_id,)),)
    resource = replace(state.resource, category=category or "")
    rule = book.by_category.get(category)
    rule_id = rule.rule_id if rule else "SPEC_ACTIVE_FLOW" if category == "DATA_FLOW" else ""
    action = rule.action if rule else "DISABLE" if category == "DATA_FLOW" else ""

    def unknown(code):
        return Assessment(resource, category or "", rule_id, action, "UNKNOWN",
                          uncertainties=(Uncertainty(code, "policy or state prerequisite is not established"),))

    def citation(groups):
        intersection = None
        for group in groups:
            if not group:
                continue
            sources = {observations[oid].evidence.evidence_id for fact in group for oid in fact.observation_ids
                       if oid in observations and observations[oid].evidence.citeable}
            intersection = sources if intersection is None else intersection & sources
        return min(intersection) if intersection else None

    def outcome(violation, finding, remedy, verification, proof, condition_proof=(), retained=False, conjunctive=False):
        # Cite a direct state witness. Separately sourced, time-qualified policy
        # prerequisites remain in the internal derivation; they need not occur
        # in that same artifact. Required state fields still need a joint witness.
        supporting = proof
        groups = tuple((f,) for f in supporting) if not violation or conjunctive else (proof,)
        evidence = citation(groups)
        if evidence is None:
            return unknown("NO_SINGLE_SUPPORTING_CITATION")
        rationale = "Supplied policy applied to an eligible direct observation"
        def op(name, cited):
            return OperationDerivation(name, resource.system_id, resource.resource_id, evidence if cited else "", rule_id, rationale)
        operations = (op(finding, True), op(remedy, False), op(verification, False)) if violation else (op(verification, True),)
        if retained:
            operations += (op("VERIFY_RECORD_PRESENT", not violation),)
        ids = tuple(sorted({oid for f in proof + condition_proof for oid in f.observation_ids}))
        return Assessment(resource, category, rule_id, action, "VIOLATION" if violation else "COMPLIANT", operations, ids)

    if not category or not action:
        return unknown("UNMAPPED_POLICY_CATEGORY")
    protected = {"ACCOUNT_TOMBSTONE": "REDACT", "SECURITY_AUDIT_LOG": "RETAIN",
                 "LEGAL_HOLD_RECORD": "RETAIN", "BACKUP_ARCHIVE": "RETAIN"}
    if category in protected and action != protected[category]:
        return unknown("CONTRACT_POLICY_CONFLICT")
    if any(f.conflicting_values for f in facts):
        return unknown("CONFLICTING_POLICY_FACTS")
    presence_facts = tuple(f for f in facts if f.dimension == "presence")
    presence = decoded(presence_facts[0]) if len(presence_facts) == 1 else ...
    if category == "DATA_FLOW":
        enabled, proof = flag(facts, "enabled")
        scheduler, scheduler_proof = flag(facts, "scheduler_registered")
        if enabled is None or (scheduler is None and scheduler_proof) or (enabled is False and scheduler is True):
            return unknown("FLOW_STATE_UNKNOWN")
        return outcome(enabled, "REPORT_ACTIVE_DATA_FLOW", "DISABLE_DATA_FLOW", "VERIFY_DATA_FLOW_DISABLED",
                       proof if enabled else proof + scheduler_proof)
    applies, condition_proof = condition(rule, facts, user, audit_at)
    if category == "EMAIL_DELIVERY_LOG" and applies is None:
        exposed_email, email_proof = pii(facts, category, aliases, user)
        if exposed_email is True:
            applies, condition_proof = True, email_proof
    satisfied_conditions = {"Record is still attributable to a user", "Log contains a user email address"}
    if applies is None or (applies is False and rule.condition not in satisfied_conditions):
        return unknown("POLICY_CONDITION_NOT_ESTABLISHED")
    if category == "BACKUP_ARCHIVE":
        allowed, proof = flag(facts, "restore_allowed")
        archive, archive_proof = flag(facts, "archive_present")
        if archive is None and not archive_proof:
            paths = named(facts, "archive_path", "archive_key")
            if any(isinstance(decoded(f), str) and decoded(f).strip() for f in paths):
                archive, archive_proof = True, paths
        if allowed is None:
            eligible_value, eligible_proof = flag(facts, "eligible")
            block, block_proof = flag(facts, "deletion_block")
            if eligible_value is True and block is False:
                allowed, proof = True, eligible_proof + block_proof
        if presence != "PRESENT" or archive is not True:
            return unknown("REQUIRED_RETAINED_RECORD_NOT_ESTABLISHED")
        if allowed is None:
            return unknown("RESTORE_STATE_UNKNOWN")
        if allowed is False and archive is not True:
            return unknown("REQUIRED_RETAINED_RECORD_NOT_ESTABLISHED")
        result = outcome(allowed, "REPORT_RESTORE_RISK", "BLOCK_RESTORE", "VERIFY_RESTORE_BLOCKED",
                         proof, condition_proof + presence_facts + archive_proof, conjunctive=True)
        return result
    if action == "RETAIN":
        if presence != "PRESENT":
            return unknown("REQUIRED_RETAINED_RECORD_NOT_ESTABLISHED")
        return outcome(False, "", "", "VERIFY_RECORD_PRESENT", presence_facts, condition_proof)
    if presence == "ABSENT":
        if action != "DELETE":
            return unknown("REQUIRED_PRESERVED_RECORD_NOT_ESTABLISHED")
        return outcome(False, "", "", "VERIFY_RECORD_ABSENT", presence_facts, condition_proof)
    if presence != "PRESENT":
        return unknown("RECORD_STATE_UNKNOWN")
    if action == "DELETE":
        return outcome(True, "REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT", presence_facts, condition_proof)
    exposed, proof = pii(facts, category, aliases, user)
    if exposed is None:
        return unknown("IDENTIFIER_COVERAGE_UNKNOWN")
    if action == "REDACT":
        return outcome(exposed, "REPORT_EXPOSED_PII", "REDACT_RECORD", "VERIFY_RECORD_REDACTED",
                       proof if exposed else proof + presence_facts, condition_proof)
    return outcome(exposed, "REPORT_EXPOSED_PII", "ANONYMIZE_RECORD", "VERIFY_RECORD_ANONYMIZED",
                   proof if exposed else proof + presence_facts, condition_proof)
