"""Producer's registry, transcribed from problem_statement.md:101–119.

Ranks are SPEC constants, not fitted to samples. No case IDs or expected answers
belong here. The independent validator intentionally owns a separate table.
"""

from dataclasses import dataclass
from types import MappingProxyType

REQUEST_COLUMNS = ("case_id", "email", "requested_at", "reported_status",
                   "reported_at", "audit_at", "request_text")
OUTPUT_COLUMNS = ("case_id", "deletion_status", "steps_json")
STEP_FIELDS = ("step_no", "phase", "system_id", "resource_id", "operation",
               "state", "evidence_id")


@dataclass(frozen=True, slots=True)
class OperationSpec:
    phase: str
    name: str
    state: str


OPERATIONS = tuple(OperationSpec(*entry) for entry in (
    ("FINDING", "REPORT_REMAINING_RECORD", "PRESENT"),
    ("FINDING", "REPORT_EXPOSED_PII", "PRESENT"),
    ("FINDING", "REPORT_ACTIVE_DATA_FLOW", "ACTIVE"),
    ("FINDING", "REPORT_RESTORE_RISK", "ACTIVE"),
    ("REMEDIATION", "DISABLE_DATA_FLOW", "DISABLED"),
    ("REMEDIATION", "BLOCK_RESTORE", "BLOCKED"),
    ("REMEDIATION", "DELETE_RECORD", "ABSENT"),
    ("REMEDIATION", "REDACT_RECORD", "REDACTED"),
    ("REMEDIATION", "ANONYMIZE_RECORD", "ANONYMIZED"),
    ("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT"),
    ("VERIFICATION", "VERIFY_RECORD_PRESENT", "PRESENT"),
    ("VERIFICATION", "VERIFY_RECORD_REDACTED", "REDACTED"),
    ("VERIFICATION", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"),
    ("VERIFICATION", "VERIFY_DATA_FLOW_DISABLED", "DISABLED"),
    ("VERIFICATION", "VERIFY_RESTORE_BLOCKED", "BLOCKED"),
))
BY_NAME = MappingProxyType({op.name: op for op in OPERATIONS})
OPERATION_RANK = MappingProxyType({op.name: rank for rank, op in enumerate(OPERATIONS)})
