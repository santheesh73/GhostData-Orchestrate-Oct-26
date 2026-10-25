"""Exact subject/resource links with provenance and bounded trace continuation."""

from collections import defaultdict
import re

from .models import ResourceLink
from .signals import STRONG_KINDS, signals


def _subject(observation, graph, view):
    data = graph.payloads[observation.observation_id]
    if observation.claim_kind == "OPERATION_CLAIM" and data.get("event_type") == "LINK_RESOURCE_IDENTITY":
        match = re.fullmatch(r"Data catalog linked (\S+) \(([^()]*)\) to (\S+) and (\S+)\.", data.get("details", ""))
        if match and match[1] == observation.resource.resource_id and match[2] == match[4] and match[4] in view.known_users:
            return {match[4]}, "CATALOG_CLAIM", ()
        if data.get("catalog_sole_subject") is True and data.get("catalog_subject_reference") in view.known_users:
            return {data["catalog_subject_reference"]}, "CATALOG_CLAIM", ()
        return set(), "", ()
    users, aliases, references = signals(graph.payloads[observation.observation_id], view.known_users)
    if users:
        return set(users), "STABLE_REFERENCE", ()
    owners = []
    for kind, value in aliases:
        owners.extend(view.possible_owners(kind, value, observation.observed_at))
    for reference in references:
        for kind in STRONG_KINDS:
            owners.extend(view.possible_owners(kind, reference, observation.observed_at))
    if owners:
        users = {o.user_id for o in owners}
        certain = any(o.certain and o.basis != "SNAPSHOT_CONTEXT" for o in owners)
        proof = tuple(sorted({oid for owner in owners for oid in owner.observation_ids}))
        return users, "IDENTIFIER_OWNERSHIP" if certain else "CONTEXT_IDENTIFIER", proof
    # Dedicated catalog grammar supplies a linkage claim, never proof that an
    # operation succeeded or that a record has a particular state.
    return set(), "", ()


def link_resources(observations, graph, view, subject):
    from .temporal_replay import extract_facts
    direct = {o.observation_id: _subject(o, graph, view) for o in observations}
    traces = defaultdict(list)
    for observation in observations:
        if observation.trace_id:
            key = (observation.evidence.evidence_id, observation.resource.system_id,
                   observation.resource.physical_copy, observation.trace_id)
            traces[key].append(observation)
    records = defaultdict(list)
    for observation in observations:
        if not observation.resource.system_id or not observation.resource.resource_id:
            continue
        users, basis, ownership_proof = direct[observation.observation_id]
        if not users and observation.trace_id:
            key = (observation.evidence.evidence_id, observation.resource.system_id,
                   observation.resource.physical_copy, observation.trace_id)
            proofs = [other for other in traces[key] if other.observed_at <= observation.observed_at
                      and direct[other.observation_id][0]]
            users = set().union(*(direct[o.observation_id][0] for o in proofs)) if proofs else set()
            if users:
                bases = {direct[o.observation_id][1] for o in proofs}
                basis = "TRACE_CONTEXT" if bases <= {"CONTEXT_IDENTIFIER", "CATALOG_CLAIM"} else "TRACE_LOOKUP"
                records[(observation.resource.system_id, observation.resource.resource_id)].extend(
                    (direct[o.observation_id][0], direct[o.observation_id][1],
                     (o.observation_id,) + direct[o.observation_id][2]) for o in proofs)
        if users:
            records[(observation.resource.system_id, observation.resource.resource_id)].append(
                (users, basis, (observation.observation_id,) + ownership_proof))
    result = []
    for (system, resource), proofs in sorted(records.items()):
        users = set().union(*(p[0] for p in proofs))
        if subject not in users:
            continue
        bases = tuple(sorted({p[1] for p in proofs}))
        if len(users) > 1:
            status = "AMBIGUOUS"
        elif all(b in {"CONTEXT_IDENTIFIER", "TRACE_CONTEXT", "CATALOG_CLAIM"} for b in bases):
            readbacks = [o for o in observations if o.resource.system_id == system and o.resource.resource_id == resource
                         and extract_facts(o)]
            status = "LINKED" if "CATALOG_CLAIM" in bases and readbacks else "PROVISIONAL"
        else:
            status = "LINKED"
        result.append(ResourceLink(system, resource, tuple(sorted(users)), status,
                                   tuple(sorted({oid for p in proofs for oid in p[2]})), bases))
    return tuple(result)
