"""Map already-resolved decisions to rows; policy/identity engines come later.

No free-text interpretation or generic fallback is performed. Every operation
retains its supplied internal rule and rationale, outside the seven public fields.
"""

from ..models import Authorization, Decision, DeletionStatus, OutputRow
from .canonicalizer import canonical_steps


class UnresolvedDecision(ValueError):
    """A case cannot honestly be published yet."""


def emit_decision(decision: Decision, *, allow_uncertainty=False) -> OutputRow:
    if not isinstance(decision.status, DeletionStatus) or (decision.uncertainties and not allow_uncertainty):
        raise UnresolvedDecision("decision is unresolved; predictions were not fabricated")
    if decision.authorization == Authorization.UNRESOLVED:
        raise UnresolvedDecision("request authorization is unresolved")
    non_deletion = decision.status == DeletionStatus.NOT_APPLICABLE
    expected_intent = Authorization.NON_DELETION if non_deletion else Authorization.DELETION
    if decision.authorization != expected_intent:
        raise UnresolvedDecision("status conflicts with request authorization")
    if non_deletion and decision.operations:
        raise UnresolvedDecision("non-deletion decisions cannot contain operations")
    if not non_deletion and decision.coverage_complete is not True and not allow_uncertainty:
        raise UnresolvedDecision("applicable decision has incomplete evidence coverage")
    if any(not d.rule_id.strip() or not d.rationale.strip() for d in decision.operations):
        raise UnresolvedDecision("operation lacks an internal rule/rationale derivation")
    return OutputRow(decision.request.case_id, decision.status.value,
                     canonical_steps(decision.operations))
