# CURRENT MEASUREMENT — final recovery evaluation, 25 October 2026

**NOT READY — CRITICAL BLOCKERS REMAIN.** The corrected engine refuses unsupported
facts and does not produce a new complete prediction file. Historical artifacts
and earlier claims are preserved under evaluation/history/ and existing commits.
Historical root/submission output is not an approved corrected candidate.

## Baseline and final comparison

| Metric | Historical9f534ca | Corrected source |
|---|---:|---:|
| Tests |413 passed|503 passed in26.04s|
| Internal resolved requests |518/518|278/518|
| Unresolved requests |0|240|
| COMPLETE / INCOMPLETE / NOT_APPLICABLE |155 /353 /10|88 /180 /10|
| Public authorization |32/32|32/32|
| Published status agreement |25/32|16/32|
| Public abstentions |7|16|
| Exact rows / sequences |5/32|1/32|
| Step precision |137/142 (96.48%)|73/73 (100%)|
| Step recall |137/193 (70.98%)|73/193 (37.82%)|
| Step F1 |81.79%|54.89%|
| Field agreement |914/1386 (65.95%)|481/1351 (35.60%)|
| Provider calls / input / output tokens |0 /0 /0|0 /0 /0|
| Estimated model-service cost |USD0|USD0|
| Hidden accuracy / extraction recall |NOT MEASURED|NOT MEASURED|


Coverage decreases because presence no longer supplies policy conditions and
missing document fields no longer become fabricated observations. This is an
accepted safety correction with a measured coverage/recall regression, not an
answer-accuracy improvement claim. Of the73 published steps, none is extra by
public multiset comparison; whole-case exact agreement is only1/32. Diagnostic
candidate steps remain separate and are not final predictions.

Runtime paths finish inference and gates before opening previously inspected
public labels. This is a public development set, not a held-out score. Full-input
statuses are computed internal outcomes, not hidden accuracy. The augmented run
accounts for94 manifest sources and15 locally captured PDF/PNG artifacts; parsing
does not establish complete semantic interpretation. Structured-only mode still
publishes0/32 because deferred documents prevent corpus coverage.

## Actual commands and checkpoints

- Baseline tests:413 passed in17.37s; baseline public command exits1 with25/32
  published statuses and5/32 exact rows; baseline full audit/publication exit0.
- New counterexamples before repairs:20 failed,10 passed. The original failing
  classes include invented IDs/nulls, sole ownership, retention/holds, excerpts,
  inactive tombstones, restore presence and ID-derived categories.
- Corrected full suite:503 passed in26.04s. Independent fixtures include source
  row bindings, typed/log contexts, live connector evidence, policy conditions,
  conflicting owners, current/historical clocks and malformed packaging.
- python -B code/evaluation/main.py --audit-samples --with-extraction: native
  offline results shown here; imperfect comparison exits1 by design.
- Full diagnostic measured by run_audits:518 processed;278 resolved,240 unresolved.
  Observed total55.277s includes ingestion and audit.
  This was a single observation with competing verification processes, not a
  controlled speed benchmark. No new speedup claim is made.
- Source/operation/reference-clock tests and existing independent contract tests
  remain active. No official inputs or public labels were modified.

## Known unresolved scopes

These are resource scopes, not mutually exclusive case counts. Missing conditions
are UNKNOWN, not policy-false or proof of deletion.

| Unestablished scope | Count |
|---|---:|
| BACKUP_ARCHIVE:REQUIRED_RETAINED_RECORD_NOT_ESTABLISHED | 3 |
| LEGAL_HOLD_RECORD:POLICY_CONDITION_NOT_ESTABLISHED | 1 |
| SECURITY_AUDIT_LOG:POLICY_CONDITION_NOT_ESTABLISHED | 337 |
| SUPPORT_ATTACHMENT:POLICY_CONDITION_NOT_ESTABLISHED | 3 |
| SUPPORT_MESSAGE:POLICY_CONDITION_NOT_ESTABLISHED | 127 |
| UNMAPPED:RESOURCE_LINK_NOT_ESTABLISHED | 4 |
| UNMAPPED:UNMAPPED_POLICY_CATEGORY | 2 |

All240 affected evaluation cases, exact resource IDs and reasons are in
`evaluation/recovery_blockers.json`. Candidate remediation cannot be promoted
while a required condition is missing. Representative participant records include
security handover FOUND records with no retention interval, support readbacks
without established shared context, and a restore authorization without archive
readback. Four earlier explicit pre-cutoff ownership gaps remain documented in
EVIDENCE-GAPS.md. Some remaining interpretation is incomplete; not every unknown
is claimed inherently impossible to resolve.

## Public case-level disposition

| Case | Published status | Exact row | Candidate/reference steps | Failure stage / reason |
|---|---|---|---:|---|
| case_01 | ABSTAIN | FAIL | 0/1 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,NO_ASSESSED_RESOURCES,RESOURCE_STATE_COVERAGE_MISSING |
| case_02 | ABSTAIN | FAIL | 0/1 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,NO_ASSESSED_RESOURCES,RESOURCE_STATE_COVERAGE_MISSING |
| case_03 | COMPLETE | FAIL | 2/3 | FIELD,MISSING_STEP,SEQUENCE |
| case_04 | ABSTAIN | FAIL | 0/2 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,NO_ASSESSED_RESOURCES,RESOURCE_STATE_COVERAGE_MISSING |
| case_05 | INCOMPLETE | PASS | 3/3 | Exact public agreement |
| case_06 | INCOMPLETE | FAIL | 3/4 | FIELD,MISSING_STEP,SEQUENCE |
| case_07 | ABSTAIN | FAIL | 0/4 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,RESOURCE_LINK_NOT_ESTABLISHED,CATALOG_TARGET_WITHOUT_STATE,MATCHING_DOCUMENT_NOT_INTERPRETED,RESOURCE_OWNERSHIP_UNRESOLVED,RESOURCE_STATE_COVERAGE_MISSING |
| case_08 | INCOMPLETE | FAIL | 3/4 | FIELD,MISSING_STEP,SEQUENCE |
| case_09 | INCOMPLETE | FAIL | 3/5 | FIELD,MISSING_STEP,SEQUENCE |
| case_10 | INCOMPLETE | FAIL | 3/4 | FIELD,MISSING_STEP,SEQUENCE |
| case_11 | ABSTAIN | FAIL | 10/14 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_12 | ABSTAIN | FAIL | 1/5 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_13 | ABSTAIN | FAIL | 4/8 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_14 | ABSTAIN | FAIL | 4/5 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_15 | ABSTAIN | FAIL | 4/5 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,POLICY_CONDITION_NOT_ESTABLISHED,MATCHING_DOCUMENT_NOT_INTERPRETED |
| case_16 | ABSTAIN | FAIL | 6/7 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_17 | ABSTAIN | FAIL | 2/5 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,POLICY_CONDITION_NOT_ESTABLISHED,REQUIRED_RETAINED_RECORD_NOT_ESTABLISHED,RESOURCE_LINK_NOT_ESTABLISHED,UNMAPPED_POLICY_CATEGORY,CATALOG_TARGET_WITHOUT_STATE,RESOURCE_OWNERSHIP_UNRESOLVED,RESOURCE_STATE_COVERAGE_MISSING |
| case_18 | ABSTAIN | FAIL | 9/14 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_19 | ABSTAIN | FAIL | 4/8 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_20 | INCOMPLETE | FAIL | 6/8 | FIELD,MISSING_STEP,SEQUENCE |
| case_21 | COMPLETE | FAIL | 1/3 | FIELD,MISSING_STEP,SEQUENCE |
| case_22 | ABSTAIN | FAIL | 6/8 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_23 | INCOMPLETE | FAIL | 6/8 | FIELD,MISSING_STEP,SEQUENCE |
| case_24 | INCOMPLETE | FAIL | 6/7 | FIELD,MISSING_STEP,SEQUENCE |
| case_25 | COMPLETE | FAIL | 1/3 | FIELD,MISSING_STEP,SEQUENCE |
| case_26 | COMPLETE | FAIL | 4/6 | FIELD,MISSING_STEP,SEQUENCE |
| case_27 | COMPLETE | FAIL | 4/6 | FIELD,MISSING_STEP,SEQUENCE |
| case_28 | COMPLETE | FAIL | 4/6 | FIELD,MISSING_STEP,SEQUENCE |
| case_29 | INCOMPLETE | FAIL | 12/14 | FIELD,MISSING_STEP,SEQUENCE |
| case_30 | INCOMPLETE | FAIL | 12/14 | FIELD,MISSING_STEP,SEQUENCE |
| case_31 | ABSTAIN | FAIL | 1/3 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_32 | ABSTAIN | FAIL | 3/5 | POLICY_CONDITION_NOT_ESTABLISHED |

## At least three independent added cases

1. Matching subject email on an attachment with no exclusive-ownership statement:
   UNKNOWN; no DELETE_RECORD. Explicit sole_subject=true is a positive control;
   false, conflicting and multiple-owner counterparts remain blocked.
2. Security/hold record present without an effective retention/hold fact:
   UNKNOWN. Active dated retention/explicit active hold are positive controls;
   expired, malformed and conflicting facts cannot invent a delete policy.
3. Generic user panel or statement/filename suffix without a resource mapping:
   no synthetic resource. Explicit labeled deleted/redacted records and storage
   objects are positive controls, preserving only literal null/Boolean values.
4. Restore allow/deny decision without archive readback: permission is recorded;
   archive existence stays unknown. Explicit archive presence is tested separately.
5. Nonempty nested excerpt/body/notes with an address: not a redaction certificate.
   A complete finite generic-summary grammar is tested with unseen compositions,
   digits/names/extra-sentence negative controls and missing explicit PII fields.
6. Packaging rejects duplicates, extra/missing cases, wrong operations/states,
   fields/numbering/citations, forbidden members and potential credential patterns.
   Existing bundles survive failures; shape-only checks cannot publish a package.

## Failure taxonomy and limits

Coverage/identity/state gaps, policy/retention uncertainty, extraction grounding,
flow/restore evidence, missing/extra/wrong steps, evidence IDs, sequence and
packaging are distinct failures. The per-case table lists all non-exact rows.
Public comparison cannot certify hidden correctness; matching IDs/hash values
cannot certify semantic proof. No full semantic-recall benchmark, live provider,
Linux/Tesseract run, final trace export or official ranking was measured.

## Skills applied

hackerrank-orchestrate-evidence: independent counterexamples and source-bound facts;
hackerrank-orchestrate-design: existing model/code seam and failure disposition;
orchestrate-test-fix: before/fail/repair/retest and whole-output comparison;
orchestrate-submit: source/contract consistency and blocked release gate;
hackerrank-orchestrate-package: explicit inventory, fresh destinations and hashes;
orchestrate-interview: honest technical notes and constant provenance. No paid
provider, plugin installation, agent framework or external submission occurred.
