"""Policy decisions with explicit evidence coverage and publication gates."""

from collections import Counter
from dataclasses import asdict, replace
import hashlib
import json

from ..models import Authorization, Decision, DeletionStatus, Uncertainty
from ..resolve.engine import ReconstructionEngine
from ..resolve.signals import eligible
from .applicability import classify_request
from .facts import named, project
from .models import Assessment, Audit
from .obligations import assess, decoded
from .planner import assemble
from .rulebook import RuleBook


class PolicyEngine:
    def __init__(self, index, rulebook):
        self.reconstruction = ReconstructionEngine(index)
        self.observations = self.reconstruction.observations
        self.rulebook = rulebook

    def audit(self, request, *, coverage_complete=False):
        if type(coverage_complete) is not bool:
            raise ValueError("coverage premise must be an explicit Boolean")
        intent = classify_request(request.request_text)
        if intent.authorization == Authorization.NON_DELETION:
            return Audit(Decision(request, intent.authorization, DeletionStatus.NOT_APPLICABLE,
                                  coverage_complete=True), intent)
        if intent.authorization == Authorization.UNRESOLVED:
            return Audit(Decision(request, intent.authorization, uncertainties=(
                Uncertainty(intent.reason, "request authorization requires further interpretation"),)), intent)
        reconstruction = self.reconstruction.reconstruct(request)
        issues = list(reconstruction.identity.uncertainties)
        if reconstruction.identity.status != "RESOLVED":
            issues.append(Uncertainty("IDENTITY_NOT_TIME_QUALIFIED", "request identity needs corroboration"))
        assessments, dependencies = [], []
        links = {(link.system_id, link.resource_id): link for link in reconstruction.links}
        for state in reconstruction.states:
            link = links[(state.resource.system_id, state.resource.resource_id)]
            if link.status != "LINKED" or reconstruction.identity.status != "RESOLVED":
                assessments.append(Assessment(state.resource, "", "", "", "UNKNOWN", uncertainties=(
                    Uncertainty("RESOURCE_LINK_NOT_ESTABLISHED", "policy cannot authorize changing a provisional or ambiguous subject resource"),)))
                continue
            if any(eligible(o, request.audit_at) != "ELIGIBLE" for o in state.timeline):
                issues.append(Uncertainty("INELIGIBLE_RECONSTRUCTION", "state contains an unavailable observation"))
                continue
            assessment = assess(state, self.rulebook, reconstruction.identity.user_id,
                                reconstruction.identity.ownership, request.audit_at, self.observations)
            assessments.append(assessment)
            # Dependencies require explicit typed endpoints, never a guessed ID
            # relationship or a global SYNC SUCCESS message.
            facts = project(state)
            endpoints = {}
            for key in ("source_system", "source_resource_id", "target_system", "target_resource_id"):
                matches = named(facts, key)
                if len(matches) == 1 and isinstance(decoded(matches[0]), str):
                    endpoints[key] = decoded(matches[0])
            if len(endpoints) == 4:
                dependencies.append(((endpoints["source_system"], endpoints["source_resource_id"]),
                                     (endpoints["target_system"], endpoints["target_resource_id"])))
        if not assessments:
            issues.append(Uncertainty("NO_ASSESSED_RESOURCES", "an empty search cannot establish deletion completeness"))
        for assessment in assessments:
            issues.extend(assessment.uncertainties)
        if not coverage_complete:
            issues.append(Uncertainty("EVIDENCE_COVERAGE_NOT_ESTABLISHED", "all relevant copies and evidence are not yet accounted for"))
        incomplete = any(a.outcome == "VIOLATION" for a in assessments)
        operations, planning_issues = assemble(assessments, incomplete, dependencies)
        issues.extend(planning_issues)
        issues = tuple(sorted(set(issues), key=lambda u: (u.code, u.detail)))
        status = (DeletionStatus.INCOMPLETE if incomplete else DeletionStatus.COMPLETE) if not issues else None
        decision = Decision(request, intent.authorization, status, operations if status else (), issues,
                            coverage_complete=coverage_complete and not issues)
        identity_proof = tuple(sorted({oid for owner in reconstruction.identity.ownership
            if owner.basis != "SNAPSHOT_CONTEXT" for oid in owner.observation_ids}))
        return Audit(decision, intent, tuple(assessments), operations, identity_proof)


def audit_dataset(bundle, rulebook, requests):
    engine = PolicyEngine(bundle.index, rulebook)
    # Phase 02 inventory scopes explicitly say completeness NOT_ESTABLISHED.
    # File parse success cannot turn that into exhaustive subject coverage.
    audits = []
    for request in sorted(requests, key=lambda r: r.case_id):
        try:
            audits.append(engine.audit(request))
        except (ValueError, TypeError, OSError) as exc:
            intent = classify_request(request.request_text)
            audits.append(Audit(Decision(request, intent.authorization, uncertainties=(
                Uncertainty("CASE_PROCESSING_FAILED", "case isolated after " + type(exc).__name__),)), intent))
    return tuple(audits)


def audit_summary(bundle, audits):
    cases = [{"case_id": a.decision.request.case_id, "authorization": a.intent.authorization.value,
              "intent_reason": a.intent.reason, "deletion_status": a.decision.status.value if a.decision.status else None,
              "assessment_counts": dict(sorted(Counter(s.outcome for s in a.assessments).items())),
              "candidate_operations": len(a.candidate_operations),
              "uncertainty_codes": sorted({u.code for u in a.decision.uncertainties})} for a in audits]
    # Bind source/condition/operation provenance without exposing PII in stdout.
    proof = {"sources": sorted((r.source.path, r.source_sha256) for r in (*bundle.files, *bundle.context)),
             "audits": [{"decision": asdict(a.decision), "assessments": [asdict(s) for s in a.assessments],
                         "identity_proof": a.identity_observation_ids} for a in audits]}
    encoded = json.dumps(proof, default=lambda value: value.isoformat(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {"phase": "04", "request_count": len(audits),
            "resolved_count": sum(a.decision.status is not None for a in audits),
            "unresolved_count": sum(a.decision.status is None for a in audits),
            "status_counts": dict(sorted(Counter(a.decision.status.value for a in audits if a.decision.status).items())),
            "authorization_counts": dict(sorted(Counter(a.intent.authorization.value for a in audits).items())),
            "assessment_counts": dict(sorted(Counter(s.outcome for a in audits for s in a.assessments).items())),
            "has_ingestion_errors": bundle.has_errors,
            "deferred_evidence_files": sum(r.status.value == "DEFERRED" for r in bundle.files),
            "proof_sha256": hashlib.sha256(encoded.encode()).hexdigest(), "output_written": False,
            "deletion_accuracy": "NOT_MEASURED", "audit_complete": False, "cases": cases}
