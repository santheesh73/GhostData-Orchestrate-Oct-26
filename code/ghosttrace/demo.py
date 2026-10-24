"""Entirely synthetic Phase 01 premises; no official case IDs or sample answers.

This demonstrates compilation of supplied decisions, not a deletion-audit engine.
Only the explicit --demo CLI mode imports these fixtures.
"""

from datetime import datetime, timezone

from .models import (Authorization, Decision, DeletionStatus, EvidenceSource,
                     OperationDerivation, Request)


def synthetic_cases():
    instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
    def request(name):
        return Request("synthetic_" + name, name + "@example.invalid", instant,
                       "NOT_STARTED", instant, instant, "Synthetic premise: " + name)
    catalog = {"synthetic_evidence": EvidenceSource("synthetic_evidence", instant, "synthetic")}
    def derivation(operation, system, resource, evidence=""):
        return OperationDerivation(operation, system, resource, evidence,
                                   "synthetic_rule", "Explicit synthetic premise, not dataset evidence")
    complete = request("complete")
    verifications = ("VERIFY_RECORD_ABSENT", "VERIFY_RECORD_PRESENT", "VERIFY_RECORD_REDACTED",
                     "VERIFY_RECORD_ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED", "VERIFY_RESTORE_BLOCKED")
    complete_ops = tuple(derivation(op, "synthetic_service", "verified_" + str(i), "synthetic_evidence")
                         for i, op in enumerate(verifications))
    incomplete = request("incomplete")
    operations = []
    for resource, finding, remedy, verify in (
        ("deleted", "REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT"),
        ("redacted", "REPORT_EXPOSED_PII", "REDACT_RECORD", "VERIFY_RECORD_REDACTED"),
        ("anonymous", "REPORT_EXPOSED_PII", "ANONYMIZE_RECORD", "VERIFY_RECORD_ANONYMIZED"),
        ("flow", "REPORT_ACTIVE_DATA_FLOW", "DISABLE_DATA_FLOW", "VERIFY_DATA_FLOW_DISABLED"),
        ("backup", "REPORT_RESTORE_RISK", "BLOCK_RESTORE", "VERIFY_RESTORE_BLOCKED"),
    ):
        operations.extend((derivation(finding, "synthetic_service", resource, "synthetic_evidence"),
                           derivation(remedy, "synthetic_service", resource),
                           derivation(verify, "synthetic_service", resource)))
    not_applicable = request("not_applicable")
    decisions = (
        Decision(complete, Authorization.DELETION, DeletionStatus.COMPLETE,
                 tuple(reversed(complete_ops)), coverage_complete=True),
        Decision(incomplete, Authorization.DELETION, DeletionStatus.INCOMPLETE,
                 tuple(reversed(operations)), coverage_complete=True),
        Decision(not_applicable, Authorization.NON_DELETION, DeletionStatus.NOT_APPLICABLE),
    )
    return tuple(d.request for d in decisions), decisions, catalog
