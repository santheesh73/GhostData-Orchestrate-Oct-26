"""Combine copy-specific obligations without losing retained-copy safeguards."""

from collections import defaultdict
from dataclasses import replace

from ..models import Uncertainty
from ..spec_registry import BY_NAME, OPERATION_RANK


def assemble(assessments, incomplete, dependencies=()):
    issues, by_resource = [], defaultdict(list)
    for assessment in assessments:
        by_resource[(assessment.resource.system_id, assessment.resource.resource_id)].append(assessment)
    for group in by_resource.values():
        actions = {a.action for a in group if a.outcome != "UNKNOWN"}
        if len(actions) > 1:
            issues.append(Uncertainty("INCOMPATIBLE_COPY_ACTIONS", "copies of one public resource require incompatible policy actions"))
    operations = {}
    for assessment in assessments:
        for operation in assessment.operations:
            if incomplete and BY_NAME[operation.operation].phase == "VERIFICATION":
                operation = replace(operation, evidence_id="")
            key = (operation.operation, operation.system_id, operation.resource_id)
            previous = operations.get(key)
            if previous is None or (operation.evidence_id, operation.rule_id) < (previous.evidence_id, previous.rule_id):
                operations[key] = operation
    result = tuple(sorted(operations.values(), key=lambda o: (OPERATION_RANK[o.operation], o.system_id, o.resource_id)))
    destructive = {"DELETE_RECORD", "REDACT_RECORD", "ANONYMIZE_RECORD"}
    positions = {(op.system_id, op.resource_id): i for i, op in enumerate(result) if op.operation in destructive}
    for source, downstream in dependencies:
        if source in positions and downstream in positions and positions[source] <= positions[downstream]:
            issues.append(Uncertainty("DEPENDENCY_ORDER_CONFLICT", "required downstream-first changes conflict with the canonical operation order"))
    return result, tuple(sorted(set(issues), key=lambda u: (u.code, u.detail)))
