"""Publication boundaries for explicit resolved decisions and checked audits."""

from pathlib import Path
from typing import Mapping

from .emit.csv_writer import write_output
from .emit.operation_mapper import UnresolvedDecision, emit_decision
from .models import Authorization, Decision, EvidenceSource, Request, Uncertainty


def diagnose_requests(requests: tuple[Request, ...]) -> dict:
    decisions = tuple(Decision(request, Authorization.UNRESOLVED,
                              uncertainties=(Uncertainty("POLICY_AUDIT_NOT_RUN",
                                  "Use --audit-policy to run policy diagnostics; incomplete evidence prevents publication"),))
                      for request in requests)
    return {"phase": "04", "status": "UNRESOLVED", "request_count": len(requests),
            "unresolved_count": len(decisions),
            "unresolved_case_ids": sorted(d.request.case_id for d in decisions),
            "reason": "POLICY_AUDIT_NOT_RUN", "output_written": False}


def publish_decisions(decisions: tuple[Decision, ...], requests: tuple[Request, ...],
                      catalog: Mapping[str, EvidenceSource], destination: Path, *, allow_uncertainty=False) -> Path:
    expected = {r.case_id: r for r in requests}
    if len(decisions) != len(requests) or {d.request.case_id for d in decisions} != set(expected):
        raise UnresolvedDecision("complete decision coverage is required before publication")
    if any(d.request != expected[d.request.case_id] for d in decisions):
        raise UnresolvedDecision("decision request context does not match the supplied requests")
    rows = tuple(emit_decision(decision, allow_uncertainty=allow_uncertainty) for decision in decisions)
    return write_output(rows, destination, requests, catalog, allow_empty_complete=allow_uncertainty)


def publish_policy_audits(audits, requests, catalog, destination, observations):
    from .quality.audit_gate import check_audit
    if any(check_audit(audit, observations) for audit in audits):
        raise UnresolvedDecision("audit proof/publication gate failed; existing output preserved")
    return publish_decisions(tuple(audit.decision for audit in audits), requests, catalog, destination)
