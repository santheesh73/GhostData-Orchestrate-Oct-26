"""Hand-specified public representation for the three synthetic premises.

Does not import registry, mapper, canonicalizer, or demonstration implementation.
"""


def _steps(items, *, complete=False):
    return [{"step_no": i, "phase": phase, "system_id": "synthetic_service",
             "resource_id": resource, "operation": operation, "state": state,
             "evidence_id": "synthetic_evidence" if complete or phase == "FINDING" else ""}
            for i, (phase, operation, state, resource) in enumerate(items, 1)]


def expected_demo_rows():
    complete = _steps([
        ("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT", "verified_0"),
        ("VERIFICATION", "VERIFY_RECORD_PRESENT", "PRESENT", "verified_1"),
        ("VERIFICATION", "VERIFY_RECORD_REDACTED", "REDACTED", "verified_2"),
        ("VERIFICATION", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", "verified_3"),
        ("VERIFICATION", "VERIFY_DATA_FLOW_DISABLED", "DISABLED", "verified_4"),
        ("VERIFICATION", "VERIFY_RESTORE_BLOCKED", "BLOCKED", "verified_5"),
    ], complete=True)
    incomplete = _steps([
        ("FINDING", "REPORT_REMAINING_RECORD", "PRESENT", "deleted"),
        ("FINDING", "REPORT_EXPOSED_PII", "PRESENT", "anonymous"),
        ("FINDING", "REPORT_EXPOSED_PII", "PRESENT", "redacted"),
        ("FINDING", "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", "flow"),
        ("FINDING", "REPORT_RESTORE_RISK", "ACTIVE", "backup"),
        ("REMEDIATION", "DISABLE_DATA_FLOW", "DISABLED", "flow"),
        ("REMEDIATION", "BLOCK_RESTORE", "BLOCKED", "backup"),
        ("REMEDIATION", "DELETE_RECORD", "ABSENT", "deleted"),
        ("REMEDIATION", "REDACT_RECORD", "REDACTED", "redacted"),
        ("REMEDIATION", "ANONYMIZE_RECORD", "ANONYMIZED", "anonymous"),
        ("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT", "deleted"),
        ("VERIFICATION", "VERIFY_RECORD_REDACTED", "REDACTED", "redacted"),
        ("VERIFICATION", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", "anonymous"),
        ("VERIFICATION", "VERIFY_DATA_FLOW_DISABLED", "DISABLED", "flow"),
        ("VERIFICATION", "VERIFY_RESTORE_BLOCKED", "BLOCKED", "backup"),
    ])
    return [
        {"case_id": "synthetic_complete", "deletion_status": "COMPLETE", "steps_json": complete},
        {"case_id": "synthetic_incomplete", "deletion_status": "INCOMPLETE", "steps_json": incomplete},
        {"case_id": "synthetic_not_applicable", "deletion_status": "NOT_APPLICABLE", "steps_json": []},
    ]
