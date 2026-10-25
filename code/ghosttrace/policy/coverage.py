"""Account for the finite participant corpus without claiming outside coverage.

Parsing a file alone is insufficient: unresolved subject-matching documents,
unreadable sources, provisional links and catalog targets without direct state
remain blockers. Generic partial/synthetic bundles have no corpus certificate.
"""

from dataclasses import dataclass

from ..resolve.signals import eligible, payload


@dataclass(frozen=True, slots=True)
class Coverage:
    complete: bool
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]
    resources: tuple[tuple[str, str], ...]


def certify(bundle, engine, request, reconstruction):
    blockers, sources = set(), set()
    files = getattr(bundle, "files", ())
    context = getattr(bundle, "context", ())
    required = {"user_identities.csv", "user_audit_log.csv", "system_activity.csv", "deletion_rules.csv"}
    if not files or {r.source.path for r in context} != required:
        blockers.add("CORPUS_CONTEXT_NOT_ACCOUNTED")
    if any(r.status.value != "PARSED" for r in context):
        blockers.add("CONTEXT_PARSE_INCOMPLETE")
    if reconstruction.identity.status != "RESOLVED":
        blockers.add("IDENTITY_UNRESOLVED")
    for result in files:
        clock = result.source.available_at
        if clock is not None and clock > request.audit_at:
            continue
        sources.add(result.source.evidence_id)
        if clock is None or result.status.value != "PARSED":
            blockers.add("ELIGIBLE_SOURCE_NOT_PARSED")
    linked = {(link.system_id, link.resource_id) for link in reconstruction.links}
    stated = {(state.resource.system_id, state.resource.resource_id) for state in reconstruction.states
              if state.facts}
    if not linked or not linked <= stated:
        blockers.add("RESOURCE_STATE_COVERAGE_MISSING")
    if any(link.status != "LINKED" for link in reconstruction.links):
        blockers.add("RESOURCE_OWNERSHIP_UNRESOLVED")
    # Search every strong alias through the complete ingestion index, including
    # text-only documents. A captured but uninterpreted relevant artifact cannot
    # disappear merely because it has no normalized resource ID yet.
    candidates = {}
    for owner in reconstruction.identity.ownership:
        for observation in bundle.index.lookup_identifier(owner.kind, owner.value).observations:
            candidates[observation.observation_id] = observation
    user = reconstruction.identity.user_id
    for oid in engine.reconstruction.by_user.get(user, ()):
        observation = engine.observations[oid]
        candidates[oid] = observation
    for observation in candidates.values():
        if observation.claim_kind in {"IDENTITY_REGISTRY_ENTRY", "IDENTITY_CONTEXT", "POLICY_CONTEXT"}:
            continue
        state = eligible(observation, request.audit_at)
        if state == "FUTURE":
            continue
        if state == "UNKNOWN_TIME":
            blockers.add("MATCHING_SOURCE_TIME_UNKNOWN")
            continue
        if observation.claim_kind == "RAW_UNPARSED":
            blockers.add("MATCHING_CONTENT_UNPARSED")
        if observation.claim_kind == "DOCUMENT_TEXT":
            promoted = [o for o in bundle.index.lookup_evidence(observation.evidence.evidence_id).observations
                        if o.claim_kind == "RECORD_SNAPSHOT" and (o.resource.system_id, o.resource.resource_id) in linked]
            if not promoted:
                blockers.add("MATCHING_DOCUMENT_NOT_INTERPRETED")
        data = payload(observation)
        if data.get("event_type") == "LINK_RESOURCE_IDENTITY" and data.get("catalog_subject_reference") == user:
            if (observation.resource.system_id, observation.resource.resource_id) not in stated:
                blockers.add("CATALOG_TARGET_WITHOUT_STATE")
    return Coverage(not blockers, tuple(sorted(blockers)), tuple(sorted(sources)), tuple(sorted(linked)))
