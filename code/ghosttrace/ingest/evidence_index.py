"""Exact candidate retrieval with provenance; no identity/state adjudication.

All copies and competing observations survive. Time-filtered searches report
excluded/unknown candidates; a zero-hit search never establishes absence.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from ..models import Observation
from .normalization import normalize_identifier


@dataclass(frozen=True, slots=True)
class LookupResult:
    observations: tuple[Observation, ...]
    excluded_future: int = 0
    excluded_unknown_time: int = 0
    supports_absence: bool = False


class EvidenceIndex:
    def __init__(self, observations=()):
        self._observations = {}
        self._identifiers = defaultdict(set)
        self._resources = defaultdict(set)
        self._evidence = defaultdict(set)
        self._traces = defaultdict(set)
        for observation in observations:
            self.add(observation)

    def __len__(self):
        return len(self._observations)

    @staticmethod
    def _trace_key(observation):
        return (observation.evidence.evidence_id, observation.resource.system_id,
                observation.resource.physical_copy, observation.trace_id)

    def add(self, observation):
        if not observation.observation_id:
            raise ValueError("indexed observations require a content/source-bound ID")
        previous = self._observations.get(observation.observation_id)
        if previous is not None:
            if previous != observation:
                raise ValueError("observation ID collision")
            return
        oid = observation.observation_id
        self._observations[oid] = observation
        for identifier in observation.identifiers:
            self._identifiers[(identifier.kind, normalize_identifier(identifier.kind, identifier.value))].add(oid)
        if observation.resource.resource_id:
            self._resources[observation.resource.resource_id].add(oid)
        self._evidence[observation.evidence.evidence_id].add(oid)
        if observation.trace_id:
            self._traces[self._trace_key(observation)].add(oid)

    def _result(self, ids, at=None, expand_traces=False):
        if at is not None and at.tzinfo is None:
            raise ValueError("retrieval cutoff must be timezone-aware")
        ids = set(ids)
        if expand_traces:
            for oid in tuple(ids):
                observation = self._observations[oid]
                if observation.trace_id:
                    ids.update(self._traces[self._trace_key(observation)])
        selected, future, unknown = [], 0, 0
        for oid in sorted(ids):
            observation = self._observations[oid]
            available, observed = observation.evidence.available_at, observation.observed_at
            if at is not None:
                if (available is not None and available > at) or (observed is not None and observed > at):
                    future += 1
                    continue
                if available is None or observed is None:
                    unknown += 1
                    continue
            selected.append(observation)
        return LookupResult(tuple(selected), future, unknown)

    def lookup_identifier(self, kind, value, *, at=None, expand_traces=True):
        key = (kind, normalize_identifier(kind, value))
        return self._result(self._identifiers.get(key, ()), at, expand_traces)

    def lookup_resource(self, resource_id, *, system_id=None, physical_copy=None, at=None):
        candidates = self._resources.get(resource_id, ())
        ids = [oid for oid in candidates
               if (system_id is None or self._observations[oid].resource.system_id == system_id)
               and (physical_copy is None or self._observations[oid].resource.physical_copy == physical_copy)]
        return self._result(ids, at)

    def lookup_evidence(self, evidence_id, *, at=None):
        return self._result(self._evidence.get(evidence_id, ()), at)

    def all_observations(self):
        return self._result(self._observations).observations
