"""Publication boundary. Policy inference remains deferred after Phase 03."""

from pathlib import Path
from typing import Mapping

from .emit.csv_writer import write_output
from .emit.operation_mapper import UnresolvedDecision, emit_decision
from .models import Authorization, Decision, EvidenceSource, Request, Uncertainty


def diagnose_requests(requests: tuple[Request, ...]) -> dict:
    decisions = tuple(Decision(request, Authorization.UNRESOLVED,
                              uncertainties=(Uncertainty("POLICY_ENGINE_NOT_IMPLEMENTED",
                                  "Policy decisions are deferred; use --reconstruct-evidence for identity/time diagnostics"),))
                      for request in requests)
    return {"phase": "03", "status": "UNRESOLVED", "request_count": len(requests),
            "unresolved_count": len(decisions),
            "unresolved_case_ids": sorted(d.request.case_id for d in decisions),
            "reason": "POLICY_ENGINE_NOT_IMPLEMENTED", "output_written": False}


def publish_decisions(decisions: tuple[Decision, ...], requests: tuple[Request, ...],
                      catalog: Mapping[str, EvidenceSource], destination: Path) -> Path:
    expected = {r.case_id: r for r in requests}
    if len(decisions) != len(requests) or {d.request.case_id for d in decisions} != set(expected):
        raise UnresolvedDecision("complete decision coverage is required before publication")
    if any(d.request != expected[d.request.case_id] for d in decisions):
        raise UnresolvedDecision("decision request context does not match the supplied requests")
    rows = tuple(emit_decision(decision) for decision in decisions)
    return write_output(rows, destination, requests, catalog)
