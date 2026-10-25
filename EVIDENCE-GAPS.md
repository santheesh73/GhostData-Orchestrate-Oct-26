# CURRENT LIMITATIONS — 25 October 2026 recovery

Corrected diagnostics resolve280/518;238 are unresolved. Known unsafe defaults
were removed. The exact affected cases/resources and condition codes are in
evaluation/phase06b/root_causes.json. Resource-scope counts follow; categories can
overlap within a case. Some are missing source facts, others remain incomplete
interpretation. No universal impossibility claim is made.

| Unknown prerequisite | Scopes |
|---|---:|
| BACKUP_ARCHIVE:REQUIRED_RETAINED_RECORD_NOT_ESTABLISHED | 3 |
| LEGAL_HOLD_RECORD:POLICY_CONDITION_NOT_ESTABLISHED | 1 |
| SECURITY_AUDIT_LOG:POLICY_CONDITION_NOT_ESTABLISHED | 337 |
| SUPPORT_ATTACHMENT:POLICY_CONDITION_NOT_ESTABLISHED | 3 |
| SUPPORT_MESSAGE:POLICY_CONDITION_NOT_ESTABLISHED | 75 |
| UNMAPPED:RESOURCE_LINK_NOT_ESTABLISHED | 2 |

A source schema scan found retention_until/retained_until fields on some records,
but they are not supplied in every relevant record/cutoff. A signed or present
record alone does not establish its effective retention interval. Matching a
subject identifier does not establish exclusive ownership. Restore permission
does not establish archive existence. Uninterpreted text remains unknown.

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



No clarification or corrected dataset was supplied. The earlier claim that all
518 internally resolved constituted readiness is superseded. Publication and
packaging stay blocked rather than inserting unsupported official labels. The
historical all518 CSV/bundle are preserved; they are not a safe corrected release.
A live model could assist existing artifact interpretation only with approved
configuration/budget; it cannot create missing evidence.

Phase06B investigated337 undated security scopes over202 logical resources.
No expiry was recovered for them. Explicit source-labeled order contents recover
52 support scopes; two exact catalog/document joins resolve two full cases.
All remaining gates and source classifications are in PHASE06B-REPORT.md.
