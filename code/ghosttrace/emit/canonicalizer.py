"""Order approved operation derivations; never silently delete duplicates."""

from ..models import OperationDerivation, Step
from ..spec_registry import BY_NAME, OPERATION_RANK


def canonical_steps(operations: tuple[OperationDerivation, ...]) -> tuple[Step, ...]:
    for operation in operations:
        if operation.operation not in BY_NAME:
            raise ValueError("operation derivation uses an unknown operation")
    ordered = sorted(operations, key=lambda d: (
        OPERATION_RANK[d.operation], d.system_id, d.resource_id))
    return tuple(Step(number, BY_NAME[d.operation].phase, d.system_id, d.resource_id,
                      d.operation, BY_NAME[d.operation].state, d.evidence_id)
                 for number, d in enumerate(ordered, 1))
