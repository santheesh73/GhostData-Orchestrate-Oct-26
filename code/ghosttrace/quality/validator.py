"""Independent output oracle for the documented structural contract.

Intentionally does not import the producer registry or emitter. Metadata checks
prove ID existence and cutoff eligibility only, not subject linkage or semantic
support. Those later-phase checks must not be implied by a valid contract report.
"""

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping

from ..models import EvidenceSource, Request

# Independently transcribed from problem_statement.md, Allowed Operations.
ALLOWED = (
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
)
_BY_OPERATION = {op: (phase, state, rank) for rank, (phase, op, state) in enumerate(ALLOWED)}
_FIELDS = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}
_REMEDIES = {
    "REPORT_REMAINING_RECORD": {"DELETE_RECORD"},
    "REPORT_EXPOSED_PII": {"REDACT_RECORD", "ANONYMIZE_RECORD"},
    "REPORT_ACTIVE_DATA_FLOW": {"DISABLE_DATA_FLOW"},
    "REPORT_RESTORE_RISK": {"BLOCK_RESTORE"},
}
_VERIFY = {"DELETE_RECORD": "VERIFY_RECORD_ABSENT",
           "REDACT_RECORD": "VERIFY_RECORD_REDACTED",
           "ANONYMIZE_RECORD": "VERIFY_RECORD_ANONYMIZED",
           "DISABLE_DATA_FLOW": "VERIFY_DATA_FLOW_DISABLED",
           "BLOCK_RESTORE": "VERIFY_RESTORE_BLOCKED"}


class OutputError(ValueError):
    """Malformed CSV or JSON; distinct from a validly parsed wrong answer."""


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    case_id: str
    code: str
    detail: str


@dataclass(frozen=True, slots=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]
    row_count: int
    evidence_metadata_checked: bool

    @property
    def valid(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict:
        return {"contract_valid": self.valid, "rows": self.row_count,
                "evidence_metadata_checked": self.evidence_metadata_checked,
                "semantic_support": "NOT_CHECKED",
                "issues": [asdict(issue) for issue in self.issues]}


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise OutputError("duplicate JSON object key")
        result[key] = value
    return result


def _nonfinite(_value: str):
    raise OutputError("non-finite JSON number")


def read_output(path: Path) -> list[dict]:
    """Read exact CSV framing and strict JSON, without normalizing wrong values."""
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            if next(reader, None) != ["case_id", "deletion_status", "steps_json"]:
                raise OutputError("output header must be case_id,deletion_status,steps_json")
            rows = []
            for number, values in enumerate(reader, 2):
                if len(values) != 3 or any("\x00" in value for value in values):
                    raise OutputError(f"malformed output CSV row {number}")
                steps = json.loads(values[2], object_pairs_hook=_unique_object,
                                   parse_constant=_nonfinite)
                if type(steps) is not list or any(type(step) is not dict for step in steps):
                    raise OutputError(f"row {number}: steps_json must be an array of objects")
                rows.append({"case_id": values[0], "deletion_status": values[1], "steps_json": steps})
            return rows
    except OutputError:
        raise
    except (OSError, UnicodeError, csv.Error, ValueError, RecursionError) as exc:
        raise OutputError(f"cannot read valid output CSV/JSON ({type(exc).__name__})") from None


def validate_rows(rows: Iterable[dict], requests: Iterable[Request],
                  catalog: Mapping[str, EvidenceSource] | None = None, *, allow_empty_complete=False) -> ValidationReport:
    rows, requests = list(rows), list(requests)
    expected = {request.case_id: request for request in requests}
    issues = []

    def problem(case_id, code, detail):
        issues.append(ValidationIssue(case_id, code, detail))

    if not expected or len(expected) != len(requests):
        problem("", "EXPECTED_CASES", "expected requests must be nonempty and unique")
    ids = []
    for row in rows:
        if type(row) is not dict or set(row) != {"case_id", "deletion_status", "steps_json"}:
            problem("", "ROW_FIELDS", "row must have exactly three output fields")
            continue
        case_id, status, steps = row["case_id"], row["deletion_status"], row["steps_json"]
        if type(case_id) is not str or not case_id.strip() or case_id != case_id.strip() or "\x00" in case_id:
            problem("", "CASE_ID", "case ID must be an unpadded nonempty string")
            continue
        ids.append(case_id)
        if type(status) is not str or status not in {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}:
            problem(case_id, "STATUS", "unknown deletion status")
        if type(steps) is not list or any(type(step) is not dict for step in steps):
            problem(case_id, "STEPS_TYPE", "steps must be an array of objects")
            continue
        if status == "NOT_APPLICABLE" and steps:
            problem(case_id, "STATUS_PHASES", "non-deletion must have no steps")
        if status == "COMPLETE" and ((not steps and not allow_empty_complete) or any(s.get("phase") != "VERIFICATION" for s in steps)):
            problem(case_id, "STATUS_PHASES", "complete cases require verification only")
        if status == "INCOMPLETE" and {s.get("phase") for s in steps if type(s.get("phase")) is str} != {
                "FINDING", "REMEDIATION", "VERIFICATION"}:
            problem(case_id, "STATUS_PHASES", "incomplete cases require all three phases")
        keys, valid_steps, seen_steps = [], [], set()
        for number, step in enumerate(steps, 1):
            if set(step) != _FIELDS:
                problem(case_id, "STEP_FIELDS", f"step {number} has missing or extra fields")
                continue
            if type(step["step_no"]) is not int or step["step_no"] != number:
                problem(case_id, "NUMBERING", f"step {number} must have consecutive integer numbering")
            if any(type(step[key]) is not str for key in _FIELDS - {"step_no"}):
                problem(case_id, "STEP_TYPES", f"step {number} has non-string fields")
                continue
            if any("\x00" in step[key] for key in _FIELDS - {"step_no"}):
                problem(case_id, "STEP_TYPES", f"step {number} contains a NUL character")
                continue
            if any(not step[key].strip() or step[key] != step[key].strip()
                   for key in ("system_id", "resource_id")):
                problem(case_id, "RESOURCE_ID", f"step {number} has blank or padded resource identifiers")
            operation = _BY_OPERATION.get(step["operation"])
            if operation is None:
                problem(case_id, "OPERATION", f"step {number} has an unknown operation")
                continue
            phase, state, rank = operation
            if (step["phase"], step["state"]) != (phase, state):
                problem(case_id, "OPERATION_STATE", f"step {number} has the wrong phase or state")
            keys.append((rank, step["system_id"], step["resource_id"]))
            identity = (step["operation"], step["system_id"], step["resource_id"])
            if identity in seen_steps:
                problem(case_id, "DUPLICATE_STEP", f"step {number} repeats an operation/resource")
            seen_steps.add(identity)
            valid_steps.append(step)
            cited = phase == "FINDING" or status == "COMPLETE"
            evidence_id = step["evidence_id"]
            if cited:
                if not evidence_id.strip():
                    problem(case_id, "CITATION_REQUIRED", f"step {number} needs evidence")
                elif catalog is not None:
                    source = catalog.get(evidence_id)
                    if source is None:
                        problem(case_id, "CITATION_UNKNOWN", f"step {number} cites an unknown ID")
                    elif not source.citeable:
                        problem(case_id, "CITATION_ROLE", f"step {number} cites context rather than permitted evidence")
                    elif case_id in expected:
                        try:
                            if source.available_at is None or source.available_at.tzinfo is None or source.available_at > expected[case_id].audit_at:
                                problem(case_id, "CITATION_TIME", f"step {number} evidence is not eligible at audit time")
                        except TypeError:
                            problem(case_id, "CITATION_TIME", f"step {number} evidence time metadata is invalid")
            elif evidence_id != "":
                problem(case_id, "FUTURE_CITATION", f"step {number} describes future work and must not cite evidence")
        if keys != sorted(keys):
            problem(case_id, "ORDER", "steps violate operation/system/resource order")
        if status == "INCOMPLETE":
            indexed = {(s["operation"], s["system_id"], s["resource_id"]) for s in valid_steps}
            for step in valid_steps:
                op, system, resource = step["operation"], step["system_id"], step["resource_id"]
                if op in _REMEDIES and not any((remedy, system, resource) in indexed for remedy in _REMEDIES[op]):
                    problem(case_id, "PLAN_COVERAGE", "finding lacks compatible remediation")
                if op in _VERIFY:
                    if (_VERIFY[op], system, resource) not in indexed:
                        problem(case_id, "PLAN_COVERAGE", "remediation lacks corresponding verification")
                    if not any((finding, system, resource) in indexed for finding, remedies in _REMEDIES.items() if op in remedies):
                        problem(case_id, "PLAN_COVERAGE", "remediation lacks a compatible finding")
    if ids != sorted(ids):
        problem("", "CASE_ORDER", "rows must be sorted by case_id as strings")
    if len(ids) != len(set(ids)):
        problem("", "DUPLICATE_CASE", "duplicate output case IDs")
    if set(ids) != set(expected):
        problem("", "CASE_COVERAGE", "output case IDs do not exactly match requests")
    return ValidationReport(tuple(issues), len(rows), catalog is not None)


def validate_file(path: Path, requests: Iterable[Request],
                  catalog: Mapping[str, EvidenceSource] | None = None, *, allow_empty_complete=False) -> ValidationReport:
    try:
        return validate_rows(read_output(path), requests, catalog, allow_empty_complete=allow_empty_complete)
    except OutputError as exc:
        return ValidationReport((ValidationIssue("", "OUTPUT_PARSE", str(exc)),), 0, catalog is not None)
