from dataclasses import dataclass

from ..models import Authorization, Decision, OperationDerivation, Resource, Uncertainty


@dataclass(frozen=True, slots=True)
class Intent:
    authorization: Authorization
    reason: str


@dataclass(frozen=True, slots=True)
class Rule:
    rule_id: str
    category: str
    condition: str
    action: str


@dataclass(frozen=True, slots=True)
class Assessment:
    resource: Resource
    category: str
    rule_id: str
    action: str
    outcome: str
    operations: tuple[OperationDerivation, ...] = ()
    observation_ids: tuple[str, ...] = ()
    uncertainties: tuple[Uncertainty, ...] = ()


@dataclass(frozen=True, slots=True)
class Audit:
    decision: Decision
    intent: Intent
    assessments: tuple[Assessment, ...] = ()
    candidate_operations: tuple[OperationDerivation, ...] = ()
    identity_observation_ids: tuple[str, ...] = ()
    coverage_blockers: tuple[str, ...] = ()
    coverage_source_ids: tuple[str, ...] = ()
