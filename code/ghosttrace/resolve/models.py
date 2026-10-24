"""Internal proof records. None of these are submission steps or statuses."""

from dataclasses import dataclass
from datetime import datetime

from ..models import Observation, Resource, Uncertainty


@dataclass(frozen=True, slots=True)
class Ownership:
    user_id: str
    kind: str
    value: str
    valid_from: datetime | None
    valid_until: datetime | None
    available_at: datetime | None
    observation_ids: tuple[str, ...]
    basis: str
    point: bool = False
    certain: bool = True

    def contains(self, at):
        if self.point:
            return self.valid_from == at
        return (self.valid_from is None or self.valid_from <= at) and (
            self.valid_until is None or at < self.valid_until)


@dataclass(frozen=True, slots=True)
class IdentityResolution:
    status: str
    user_id: str | None
    candidate_user_ids: tuple[str, ...]
    ownership: tuple[Ownership, ...] = ()
    uncertainties: tuple[Uncertainty, ...] = ()


@dataclass(frozen=True, slots=True)
class ResourceLink:
    system_id: str
    resource_id: str
    user_ids: tuple[str, ...]
    status: str
    observation_ids: tuple[str, ...]
    bases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StateFact:
    resource: Resource
    dimension: str
    value_json: str
    observed_at: datetime
    observation_id: str


@dataclass(frozen=True, slots=True)
class ResolvedFact:
    dimension: str
    value_json: str | None
    observed_at: datetime
    observation_ids: tuple[str, ...]
    conflicting_values: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResourceState:
    resource: Resource
    facts: tuple[ResolvedFact, ...]
    timeline: tuple[Observation, ...]
    uncertainties: tuple[Uncertainty, ...] = ()


@dataclass(frozen=True, slots=True)
class Reconstruction:
    case_id: str
    identity: IdentityResolution
    links: tuple[ResourceLink, ...]
    states: tuple[ResourceState, ...]
    uncertainties: tuple[Uncertainty, ...]
    excluded_future: int = 0
    excluded_unknown_time: int = 0
