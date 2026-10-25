"""Check policy-to-operation assembly and source eligibility before publication.

This gate does not repeat the producer's policy interpretation. Independent
structural CSV validation remains in validator.py; semantic policy behavior is
tested with handwritten fixtures. Passing source checks is not an accuracy claim.
"""

from collections import Counter
from dataclasses import replace

from ..models import Authorization, DeletionStatus
from ..resolve.signals import eligible
from ..resolve.signals import payload


def derivation_errors(observation, observations, cutoff):
    proof = payload(observation).get("extraction_proof", {})
    if not isinstance(proof, dict) or proof.get("adapter") != "EXPLICIT_CATALOG_ALIAS":
        return ()
    binding = observations.get(proof.get("catalog_observation_id"))
    if (binding is None or binding.claim_kind != "OPERATION_CLAIM" or binding.evidence.path != "system_activity.csv"
            or eligible(binding, cutoff) != "ELIGIBLE"
            or (binding.resource.system_id, binding.resource.resource_id) != (observation.resource.system_id, observation.resource.resource_id)):
        return ("DERIVED_BINDING_PROOF",)
    clocks = (binding.observed_at, binding.evidence.available_at, observation.evidence.available_at)
    if None in clocks or observation.derived_available_at is None or observation.derived_available_at < max(clocks):
        return ("DERIVED_BINDING_TIME",)
    data = payload(binding)
    if proof.get("alias") not in {data.get("catalog_label"), data.get("catalog_filename")}:
        return ("DERIVED_BINDING_ALIAS",)
    for span in proof.get("document_spans", ()):
        supporting = [o for o in observations.values() if o.evidence.evidence_id == observation.evidence.evidence_id
                      and o.location == span.get("locator") and o.claim_kind == "DOCUMENT_TEXT"
                      and span.get("text") in {line.strip() for line in payload(o).get("text", "").splitlines()}
                      and o.source_sha256 == observation.source_sha256]
        if supporting:
            return ()
    return ("DERIVED_DOCUMENT_SPAN",)

ALLOWED = {
    "DELETE": {"REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT"},
    "REDACT": {"REPORT_EXPOSED_PII", "REDACT_RECORD", "VERIFY_RECORD_REDACTED"},
    "ANONYMIZE": {"REPORT_EXPOSED_PII", "ANONYMIZE_RECORD", "VERIFY_RECORD_ANONYMIZED"},
    "RETAIN": {"VERIFY_RECORD_PRESENT", "REPORT_RESTORE_RISK", "BLOCK_RESTORE", "VERIFY_RESTORE_BLOCKED"},
    "DISABLE": {"REPORT_ACTIVE_DATA_FLOW", "DISABLE_DATA_FLOW", "VERIFY_DATA_FLOW_DISABLED"},
}


def check_audit(audit, observations):
    decision = audit.decision
    errors = set()
    if decision.status is None or decision.uncertainties:
        errors.add("UNRESOLVED_DECISION")
    if decision.authorization != audit.intent.authorization:
        errors.add("AUTHORIZATION_MISMATCH")
    if decision.status == DeletionStatus.NOT_APPLICABLE:
        if decision.authorization != Authorization.NON_DELETION or decision.operations or audit.assessments:
            errors.add("UNAUTHORIZED_NON_DELETION_PLAN")
        return tuple(sorted(errors))
    if decision.authorization != Authorization.DELETION or decision.coverage_complete is not True:
        errors.add("AUDIT_PREREQUISITE_MISSING")
    if not audit.identity_observation_ids or not audit.assessments:
        errors.add("AUDIT_PROOF_MISSING")
    for oid in audit.identity_observation_ids:
        observation = observations.get(oid)
        registry = (observation is not None and observation.claim_kind == "IDENTITY_REGISTRY_ENTRY"
                    and observation.evidence.path == "user_identities.csv" and not observation.evidence.citeable
                    and observation.observed_at is not None and observation.observed_at <= decision.request.audit_at)
        if not registry and (observation is None or eligible(observation, decision.request.audit_at) != "ELIGIBLE"):
            errors.add("IDENTITY_PROOF_TIME")
    incomplete = any(a.outcome == "VIOLATION" for a in audit.assessments)
    if decision.status != (DeletionStatus.INCOMPLETE if incomplete else DeletionStatus.COMPLETE):
        errors.add("ASSESSMENT_STATUS_MISMATCH")
    expected = set()
    for assessment in audit.assessments:
        protected = {"ACCOUNT_TOMBSTONE": "REDACT", "SECURITY_AUDIT_LOG": "RETAIN",
                     "LEGAL_HOLD_RECORD": "RETAIN", "BACKUP_ARCHIVE": "RETAIN"}
        if assessment.category in protected and assessment.action != protected[assessment.category]:
            errors.add("PROTECTED_RECORD_ACTION")
        if assessment.outcome not in {"COMPLIANT", "VIOLATION"} or assessment.uncertainties:
            errors.add("UNRESOLVED_ASSESSMENT")
        if not assessment.observation_ids:
            errors.add("STATE_PROOF_MISSING")
        for oid in assessment.observation_ids:
            observation = observations.get(oid)
            if observation is None or eligible(observation, decision.request.audit_at) != "ELIGIBLE":
                errors.add("STATE_PROOF_TIME")
            elif observation is not None:
                errors.update(derivation_errors(observation, observations, decision.request.audit_at))
        for operation in assessment.operations:
            if assessment.action == "RETAIN" and assessment.category != "BACKUP_ARCHIVE" and operation.operation != "VERIFY_RECORD_PRESENT":
                errors.add("RETAINED_RECORD_OPERATION")
            if operation.operation not in ALLOWED.get(assessment.action, ()):
                errors.add("POLICY_ACTION_MISMATCH")
            if (operation.system_id, operation.resource_id, operation.rule_id) != (
                    assessment.resource.system_id, assessment.resource.resource_id, assessment.rule_id):
                errors.add("DERIVATION_RESOURCE_MISMATCH")
            future = incomplete and operation.operation.startswith("VERIFY_")
            operation = replace(operation, evidence_id="") if future else operation
            expected.add(operation)
            cited = operation.operation.startswith("REPORT_") or not incomplete
            if cited:
                supports = [observations[oid] for oid in assessment.observation_ids if oid in observations
                            and observations[oid].evidence.evidence_id == operation.evidence_id]
                if not supports or any(not o.evidence.citeable or o.claim_kind not in {
                        "RECORD_SNAPSHOT", "SQL_RECORD", "LOG_EVENT"} for o in supports):
                    errors.add("CITATION_DERIVATION_MISMATCH")
            elif operation.evidence_id:
                errors.add("FUTURE_CITATION")
    # Multiple copies can contribute one public operation. Deduplication keeps
    # one fully derived citation; it cannot introduce another action or target.
    actual = decision.operations
    if any(op not in expected for op in actual):
        errors.add("UNSUPPORTED_OPERATION")
    expected_keys = {(o.operation, o.system_id, o.resource_id) for o in expected}
    actual_keys = [(o.operation, o.system_id, o.resource_id) for o in actual]
    if set(actual_keys) != expected_keys or any(n != 1 for n in Counter(actual_keys).values()):
        errors.add("PLAN_COVERAGE_MISMATCH")
    return tuple(sorted(errors))
