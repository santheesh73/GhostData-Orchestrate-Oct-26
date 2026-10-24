"""Phase 03 integration and PII-free diagnostics, without deletion decisions."""

from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib

from ..ingest.normalization import canonical_json, normalize_identifier
from ..models import Uncertainty
from .identity_graph import IdentityGraph
from .models import Reconstruction
from .resource_links import link_resources
from .signals import STRONG_KINDS, eligible
from .temporal_replay import replay


class ReconstructionEngine:
    def __init__(self, index):
        self.index = index
        self.graph = IdentityGraph(index.all_observations())
        self.by_user, self.by_alias = defaultdict(set), defaultdict(set)
        for oid, (users, aliases, references) in self.graph.subject_signals.items():
            for user in users:
                self.by_user[user].add(oid)
            for alias in aliases:
                self.by_alias[alias].add(oid)
            for reference in references:
                for kind in STRONG_KINDS:
                    self.by_alias[(kind, normalize_identifier(kind, reference))].add(oid)
        self.observations = {o.observation_id: o for o in self.graph.observations}

    def reconstruct(self, request):
        view = self.graph.at(request.audit_at)
        identity = view.resolve(request)
        if identity.user_id is None:
            return Reconstruction(request.case_id, identity, (), (), identity.uncertainties)
        ids = set(self.by_user.get(identity.user_id, ()))
        for owner in identity.ownership:
            ids.update(self.by_alias.get((owner.kind, owner.value), ()))
            # The ingestion index also retains dedicated catalog references.
            ids.update(o.observation_id for o in self.index.lookup_identifier(owner.kind, owner.value).observations)
        seeds = [self.observations[oid] for oid in sorted(ids)]
        trace_key = lambda o: (o.evidence.evidence_id, o.resource.system_id, o.resource.physical_copy, o.trace_id)
        traces = {trace_key(o) for o in seeds if o.trace_id}
        # Trace expansion remains confined to file, service and instance. A
        # later event cannot supply identity to an earlier result.
        seeds.extend(o for o in self.graph.observations if o.observation_id not in ids
                     and o.trace_id and trace_key(o) in traces)
        candidates = {o.observation_id: o for o in seeds}
        eligible_seeds = [o for o in seeds if eligible(o, request.audit_at) == "ELIGIBLE"]
        links = link_resources(eligible_seeds, self.graph, view, identity.user_id)
        for link in links:
            for observation in self.index.lookup_resource(link.resource_id, system_id=link.system_id).observations:
                candidates[observation.observation_id] = observation
        selected = [o for o in candidates.values() if eligible(o, request.audit_at) == "ELIGIBLE"]
        links = link_resources(selected, self.graph, view, identity.user_id)
        keys = {(link.system_id, link.resource_id) for link in links}
        states = replay([o for o in selected if (o.resource.system_id, o.resource.resource_id) in keys], request.audit_at)
        issues = list(identity.uncertainties)
        if any(link.status == "AMBIGUOUS" for link in links):
            issues.append(Uncertainty("AMBIGUOUS_RESOURCE_OWNER", "resource observations identify competing subjects"))
        if any(link.status == "PROVISIONAL" for link in links):
            issues.append(Uncertainty("PROVISIONAL_RESOURCE_LINK", "resource linkage needs time-qualified corroboration"))
        if not links:
            issues.append(Uncertainty("NO_LINKED_RESOURCES", "no resource link established; this does not prove absence"))
        issues.extend(issue for state in states for issue in state.uncertainties)
        counts = Counter(eligible(o, request.audit_at) for o in candidates.values())
        return Reconstruction(request.case_id, identity, links, states,
            tuple(sorted(set(issues), key=lambda u: (u.code, u.detail))), counts["FUTURE"], counts["UNKNOWN_TIME"])


def proof_fingerprint(result):
    """Hash internal proofs without printing identifiers or source payloads."""
    data = {"case_id": result.case_id, "identity": asdict(result.identity),
            "links": [asdict(link) for link in result.links],
            "states": [{"resource": asdict(state.resource), "facts": [asdict(fact) for fact in state.facts],
                        "timeline": sorted(o.observation_id for o in state.timeline),
                        "uncertainties": [asdict(u) for u in state.uncertainties]} for state in result.states],
            "uncertainties": [asdict(u) for u in result.uncertainties]}
    # datetime has a stable explicit-zone serialization; all other values are
    # immutable typed records/strings. Exclusion counts are diagnostics only.
    import json
    encoded = json.dumps(data, default=lambda value: value.isoformat(), sort_keys=True,
                         ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def reconstruction_summary(bundle, requests):
    engine = ReconstructionEngine(bundle.index)
    results = tuple(engine.reconstruct(request) for request in sorted(requests, key=lambda r: r.case_id))
    cases = [{"case_id": r.case_id, "identity_status": r.identity.status,
              "identity_candidates": len(r.identity.candidate_user_ids), "resource_links": len(r.links),
              "resource_copies": len(r.states), "state_facts": sum(len(s.facts) for s in r.states),
              "conflicting_facts": sum(bool(f.conflicting_values) for s in r.states for f in s.facts),
              "uncertainty_codes": sorted({u.code for u in r.uncertainties}),
              "excluded_future": r.excluded_future, "excluded_unknown_time": r.excluded_unknown_time,
              "proof_sha256": proof_fingerprint(r)} for r in results]
    return {"phase": "03", "request_count": len(results), "audit_complete": False,
            "identity_status_counts": dict(sorted(Counter(r.identity.status for r in results).items())),
            "link_status_counts": dict(sorted(Counter(link.status for r in results for link in r.links).items())),
            "resource_copies": sum(len(r.states) for r in results),
            "conflicting_facts": sum(c["conflicting_facts"] for c in cases),
            "deferred_evidence_files": sum(r.status.value == "DEFERRED" for r in bundle.files),
            "has_ingestion_errors": bundle.has_errors, "policy_status": "NOT_IMPLEMENTED",
            "identity_accuracy": "NOT_MEASURED", "temporal_accuracy": "NOT_MEASURED",
            "deletion_accuracy": "NOT_MEASURED", "output_written": False,
            "proof_sha256": hashlib.sha256(canonical_json([c["proof_sha256"] for c in cases]).encode()).hexdigest(),
            "cases": cases}
