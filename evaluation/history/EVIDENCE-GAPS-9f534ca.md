# Phase 06 evidence gaps and recommendation

## Current outcome

The requested repair reduces unresolved full-input audits from 508 to **143**;
375 are resolved internally. Public authorization is 32/32, published status
agreement 16/32, exact ordered output 2/32. Unresolved cases are failures, not
successful deletions. No final 518-row prediction file exists.

The user confirmed no official clarification/corrected dataset is available.
Recommendation: keep the official data unchanged, preserve the evidence/cutoff
rules, and keep the Phase 06 readiness gate open. Seek organizer clarification
for the concrete linkage/policy omissions below if available; do not reconstruct
IDs from case/user number suffixes or copy the public expected answer into code.
No message was sent to organizers. Additional semantic interpretation work is
still needed for some artifacts; this report does not claim every remaining
failure has been proved impossible to solve.

## Reproducible linkage examples

These examples were identified using the already-public development reference;
they are investigation evidence only and never participate in runtime inference.
A full scan of normalized participant resource observations found:

| Example | Observed participant evidence | Missing link |
|---|---|---|
| case_01 / account_001 | system_activity.csv line 3343 (activity_3342) contains DELETE_RECORD and a target, without a subject identifier. The cited SQL evidence_54 has no row for that target. | Explicit binding between this request subject and the resource ID. A missing SQL row cannot establish who the absent resource belonged to. |
| case_02 / account_002 | system_activity.csv line 3377 (activity_3376) has the same linkage gap. | An identity-to-resource binding, independent of matching numeric suffixes or temporal proximity. |
| case_03 / analytics_9406 | evidence_94 lines 42–43 have lookup_key=null and cleared subject fields; activity_3852 is an anonymization claim without a subject. | An eligible prior ownership link for the anonymized resource. |
| case_26 / account_5684 | evidence_92 has a null-profile 404 readback but no subject. evidence_02 has the earlier identifying record, but was captured 17 September 12:00 UTC, after this case's 15 September 12:00 UTC cutoff. | An identity link actually available by audit_at, or an official correction to availability metadata. |

No after-cutoff artifact was used to fill those links. The source audit is
reproducible from the listed IDs/paths and audit times. Raw private diagnostics
are under ignored .ghosttrace/phase06-repair/, with no organizer-only files read.

## Remaining native assessment gaps

Counts below are **resource scopes**, which can overlap within the 143 unresolved
cases. UNKNOWN means the implementation has not established the condition; it
is not a hidden truth label or proof of deletion.

| Category | Unestablished fact | Scopes |
|---|---|---:|
| BACKUP_ARCHIVE | POLICY_CONDITION_NOT_ESTABLISHED | 2 |
| BACKUP_ARCHIVE | REQUIRED_RETAINED_RECORD_NOT_ESTABLISHED | 1 |
| DATA_FLOW | FLOW_STATE_UNKNOWN | 7 |
| LEGAL_HOLD_RECORD | POLICY_CONDITION_NOT_ESTABLISHED | 1 |
| SECURITY_AUDIT_LOG | POLICY_CONDITION_NOT_ESTABLISHED | 87 |
| SUPPORT_ATTACHMENT | POLICY_CONDITION_NOT_ESTABLISHED | 3 |
| SUPPORT_MESSAGE | IDENTIFIER_COVERAGE_UNKNOWN | 13 |
| SUPPORT_MESSAGE | POLICY_CONDITION_NOT_ESTABLISHED | 51 |
| UNMAPPED | RESOURCE_LINK_NOT_ESTABLISHED | 2 |
| UNMAPPED | UNMAPPED_POLICY_CATEGORY | 1 |

Corpus checks additionally report 11 cases without complete linked resource
state, 6 with matching documents not fully interpreted, 2 catalog targets without
state, and 2 unresolved resource-ownership checks. These sets overlap.

Priorities are: explicit pre-cutoff subject/resource bindings for deidentified or
absent records; retention/shared-context/sole-subject facts required by policy;
remaining narrative/document interpretation; and supported interpretation of
ambiguous process/restore controls. A configured model may assist reading
available business artifacts, but cannot supply facts absent from those artifacts.

## Publication decision

Two fresh --run --with-extraction processes exit 3 with identical entire reports:
115 COMPLETE, 250 INCOMPLETE, 10 NOT_APPLICABLE, 143 unresolved. The root output
remains absent. The independent atomic writer still requires all 518 checked
cases; existing files survive a blocked run. No fake NOT_APPLICABLE/COMPLETE rows,
partial root CSV, code.zip or submission package was generated.

Verified Phase 06 code improvements remain separate from any claim of full
completion. **Phase 06 is not complete while this exit gate fails.**
