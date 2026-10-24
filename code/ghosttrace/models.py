"""Typed internal state. These records do not infer identity, policy, or intent.

Dataclasses describe boundaries; input and output validators enforce contracts.
Unknown processing state must never be serialized as an official status.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DeletionStatus(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Phase(str, Enum):
    FINDING = "FINDING"
    REMEDIATION = "REMEDIATION"
    VERIFICATION = "VERIFICATION"


class Authorization(str, Enum):
    DELETION = "DELETION"
    NON_DELETION = "NON_DELETION"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class Request:
    case_id: str
    email: str
    requested_at: datetime
    reported_status: str
    reported_at: datetime
    audit_at: datetime
    request_text: str


@dataclass(frozen=True, slots=True)
class Identifier:
    kind: str
    value: str
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Identity:
    user_id: str
    identifiers: tuple[Identifier, ...]


@dataclass(frozen=True, slots=True)
class Resource:
    system_id: str
    resource_id: str
    category: str
    physical_copy: str = ""


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    evidence_id: str
    available_at: datetime
    source_kind: str
    path: str = ""


@dataclass(frozen=True, slots=True)
class Observation:
    resource: Resource
    evidence: EvidenceSource
    observed_at: datetime
    claim_kind: str
    facts: tuple[tuple[str, str], ...]
    location: str


@dataclass(frozen=True, slots=True)
class Obligation:
    resource: Resource
    rule_id: str
    required_action: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Risk:
    resource: Resource
    kind: str
    active: bool
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Uncertainty:
    code: str
    detail: str


@dataclass(frozen=True, slots=True)
class OperationDerivation:
    operation: str
    system_id: str
    resource_id: str
    evidence_id: str
    rule_id: str
    rationale: str


@dataclass(frozen=True, slots=True)
class Decision:
    request: Request
    authorization: Authorization
    status: DeletionStatus | None = None
    operations: tuple[OperationDerivation, ...] = ()
    uncertainties: tuple[Uncertainty, ...] = ()
    coverage_complete: bool = False


@dataclass(frozen=True, slots=True)
class Step:
    step_no: int
    phase: str
    system_id: str
    resource_id: str
    operation: str
    state: str
    evidence_id: str

    def as_dict(self) -> dict:
        return {"step_no": self.step_no, "phase": self.phase,
                "system_id": self.system_id, "resource_id": self.resource_id,
                "operation": self.operation, "state": self.state,
                "evidence_id": self.evidence_id}


@dataclass(frozen=True, slots=True)
class OutputRow:
    case_id: str
    deletion_status: str
    steps: tuple[Step, ...]

    def as_dict(self) -> dict:
        return {"case_id": self.case_id, "deletion_status": self.deletion_status,
                "steps_json": [step.as_dict() for step in self.steps]}
