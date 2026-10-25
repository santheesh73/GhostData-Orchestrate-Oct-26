# Phase06B — evidence recovery and exact-output audit, 25 October 2026

## A. Git state and protected baseline

Started from clean main atd302f177cdedabd7e30f97ea49cdac09fce80b8d. The original
stash and historical submission remain preserved. No old stash was applied.
Current changes are Phase06B incremental repairs, not a restarted architecture.
Final source checkpoint/reproduction evidence is appended after verification.

## B. Reproduced baseline

Actual baseline commands: python -B -m pytest -q -p no:cacheprovider code/tests
(exit0,503 passed in20.97s); public augmented evaluator(exit1,16/32 statuses,
1/32 exact); full augmented audit(exit3,278 resolved/240 unresolved); guarded
full --run(exit3). Timings with startup were25.558s,8.541s,48.731s,53.303s.
The imperfect evaluation exit is expected, not an infrastructure crash.
Official participant-file inventory remains unchanged; old artifacts are not used
as correctness evidence. Raw logs are under .ghosttrace/phase06b/.

## C. Root causes ranked and blocker reduction

| Root cause | Baseline distinct cases / scopes | Current distinct cases / scopes | Source availability and confidence | Expected/observed exact effect; risk; complexity |
|---|---|---|---|---|
|Security retention interval absent|202 /337|202 /337|No interval on these indexed resources; high confidence in missing-condition diagnosis|No source-backed date recovery; exact effect unknown; inventing dates is unacceptable|
|Shared-context recognition|92 /127|69 /75|Explicit order-content prose exists on a subset; high confidence in scoped parser|52 scopes recovered; no published exact change because other obligations block; moderate parser risk, small code change|
|Unlinked/missing resource state|6 corpus/link cases plus overlaps|2 unlinked scopes plus corpus gaps|Some explicit catalog aliases are available; other absent-profile bindings missing|Two full cases resolved, no public exact change; multi-source timing/alias risk, moderate complexity|
|Exclusive attachment ownership|3 /3|3 /3|An additional cataloged object has explicit exclusivity; these three other records do not|No false borrowing across resources; no inferred sole ownership|
|Archive existence|3 /3|3 /3|Permission/eligibility is explicit; direct archive existence missing|Permission facts preserved without making archive-present; no public exact gain|


These groups overlap and physical copies are not distinct requests. Complete
case/resource/copy/rule/fact/provenance matrices are in evaluation/phase06b/:
baseline_root_causes.json, root_causes.json and ranked_causes.json. Coverage-only
cases explicitly have no established resource ID; no ID is invented to fill a cell.
Source facts, missing fields and unstructured interpretation are distinct. Current
unknown scopes:337 security retention,75 support context,3 exclusive attachment,
3 archive presence,1 legal hold and2 unlinked scopes. The initial477 unknown
resource scopes reduce to421. No claim that all remaining unknowns are impossible
is made, but the dominant undated records cannot acquire a date from code alone.

## D. Retention investigation and multi-source proof

Inspected normalized structured metadata, raw SQL record bodies, the signed
journal extract and security console captures.337 affected scopes over202 logical
resources have no supplied retention interval in their indexed resource evidence.
They are not mistaken for expired records. Other supplied retention_until values
and the signed extract's explicit retain-until date were already recognized.
No hidden policy table, generator or external guessed duration is used.

A real internal restriction was found: a separately sourced, eligible retention
condition and a current same-copy readback were rejected unless both appeared in
one artifact. The corrected derivation cites the direct current-state witness
and retains all supporting policy observation IDs/times. State-field conjuncts
still require a joint witness. Future/expired/other-copy controls remain blocked.
This repairs a generalized proof defect, but does not resolve any of the337
missing-interval scopes. TRUE, FALSE/outside-period and UNKNOWN remain distinct
condition results; a false retention condition does not invent a delete policy.

## E. Shared-context recovery

A source-labeled declarative order-content section establishes retained order
context even when another sentence exposes an email. Keyword-only, empty,
negated and quoted examples are rejected. This interpretation is independent of
negative PII certification: identifying text still produces REDACT_RECORD.
A selected support-console record can also supply its literal order reference;
ambiguous multiple references are not assigned to it.127 blocked scopes reduce
to75 across69 remaining cases. No generic ticket-presence fallback was restored.

## F. Identity, documents and lower-frequency gaps

Explicit catalog records bind a literal customer-statement reference to an export
ID and a literal storage filename to an object ID. Numeric suffixes are never
used. Derived observations retain original capture/observation times plus a
separate not-before time=max(document capture,catalog observation/availability).
Future catalog knowledge cannot influence an earlier audit. Reused aliases become
unresolved at the first conflicting binding; independent proof checks verify the
catalog source, exact alias, document span/hash and timing. Case33 and61 are newly
resolved from explicit joins; the same mechanism supports an additional candidate
plan in public case07, which remains unpublished because the separately identified support attachment has no established exclusive-ownership condition.

A catalog statement explicitly declaring no other subject may prove exclusivity
for that exact linked resource; it never proves presence. A separate storage
readback is mandatory. Other three attachment scopes remain unknown. Three
archive scopes still lack existence readbacks; the one legal-hold record lacks
an active/effective condition. Typed restore eligibility/block values are now
preserved without manufacturing archive presence or a phantom empty claim copy.

## G. Verification completeness

All111 public-reference verification steps were traced through discovery, linkage,
state, condition, assessment and planner emission.58 are supported/emitted;
32 stop at resource linkage,3 at state/source facts and18 at policy conditions.
No VERIFICATION_NOT_EMITTED defect was found for established obligations. The
planner already includes compliant obligations alongside violations; six new
cross-resource controls confirm absent profiles, retained audits, anonymized
analytics, tombstones, disabled flows and blocked restores. Future verification
citations are empty for INCOMPLETE; COMPLETE cites eligible state evidence.
No phantom account resources or extra numeric-pattern checks were added.

## H. Public sample comparison

| Metric | d302f17 reproduced | Phase06B |
|---|---:|---:|
|Tests|503 passed in20.97s|538 passed in24.63s|
|Full resolved / unresolved|278 /240|280 /238|
|COMPLETE / INCOMPLETE / NOT_APPLICABLE|88 /180 /10|88 /182 /10|
|Public authorization agreement|32/32|32/32|
|Published status agreement|16/32|16/32|
|Public abstentions|16|16|
|Exact rows / sequences|1/32|1/32|
|Published step precision|73/73 (100%)|73/73 (100%)|
|Published step recall|73/193 (37.82%)|73/193 (37.82%)|
|Published step F1|54.89%|54.89%|
|Field agreement|481/1351 (35.60%)|481/1351 (35.60%)|
|Candidate-only steps / matching|127 /124|130 /124|
|Candidate-only precision|97.64%|95.38%|
|Provider calls / tokens / service cost|0 /0 /USD0|0 /0 /USD0|
|Hidden accuracy / semantic extraction recall|NOT MEASURED|NOT MEASURED|


The reference labels were opened only after runtime inference/gates and were
previously inspected; this is not a holdout. Whole-case published metrics do not
improve this phase. Candidate-only precision decreases because an explicitly
cataloged stored object adds three defensible operations not listed in the public
canonical plan; these are not silently counted as true positives or predictions.
The canonical plan for case07 names a different support resource; the new stored
object is supported by its own explicit catalog/storage evidence and is not
renamed to match the label. This trade-off is ACCEPTED for evidence completeness,
not claimed as a measured score gain. All32 traces and the verification matrix
are retained, covering all16 initial public abstentions and other non-exact rows.

| Case | Current status | Candidate steps | Blocking stage / exact comparison |
|---|---|---:|---|
| case_01 | ABSTAIN | 0 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,NO_ASSESSED_RESOURCES,RESOURCE_STATE_COVERAGE_MISSING |
| case_02 | ABSTAIN | 0 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,NO_ASSESSED_RESOURCES,RESOURCE_STATE_COVERAGE_MISSING |
| case_03 | COMPLETE | 2 | FIELD,MISSING_STEP,SEQUENCE |
| case_04 | ABSTAIN | 0 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,NO_ASSESSED_RESOURCES,RESOURCE_STATE_COVERAGE_MISSING |
| case_05 | INCOMPLETE | 3 | Exact agreement |
| case_06 | INCOMPLETE | 3 | FIELD,MISSING_STEP,SEQUENCE |
| case_07 | ABSTAIN | 3 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_08 | INCOMPLETE | 3 | FIELD,MISSING_STEP,SEQUENCE |
| case_09 | INCOMPLETE | 3 | FIELD,MISSING_STEP,SEQUENCE |
| case_10 | INCOMPLETE | 3 | FIELD,MISSING_STEP,SEQUENCE |
| case_11 | ABSTAIN | 10 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_12 | ABSTAIN | 1 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_13 | ABSTAIN | 4 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_14 | ABSTAIN | 4 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_15 | ABSTAIN | 4 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,POLICY_CONDITION_NOT_ESTABLISHED,MATCHING_DOCUMENT_NOT_INTERPRETED |
| case_16 | ABSTAIN | 6 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_17 | ABSTAIN | 2 | EVIDENCE_COVERAGE_NOT_ESTABLISHED,POLICY_CONDITION_NOT_ESTABLISHED,REQUIRED_RETAINED_RECORD_NOT_ESTABLISHED,RESOURCE_LINK_NOT_ESTABLISHED,CATALOG_TARGET_WITHOUT_STATE,RESOURCE_OWNERSHIP_UNRESOLVED,RESOURCE_STATE_COVERAGE_MISSING |
| case_18 | ABSTAIN | 9 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_19 | ABSTAIN | 4 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_20 | INCOMPLETE | 6 | FIELD,MISSING_STEP,SEQUENCE |
| case_21 | COMPLETE | 1 | FIELD,MISSING_STEP,SEQUENCE |
| case_22 | ABSTAIN | 6 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_23 | INCOMPLETE | 6 | FIELD,MISSING_STEP,SEQUENCE |
| case_24 | INCOMPLETE | 6 | FIELD,MISSING_STEP,SEQUENCE |
| case_25 | COMPLETE | 1 | FIELD,MISSING_STEP,SEQUENCE |
| case_26 | COMPLETE | 4 | FIELD,MISSING_STEP,SEQUENCE |
| case_27 | COMPLETE | 4 | FIELD,MISSING_STEP,SEQUENCE |
| case_28 | COMPLETE | 4 | FIELD,MISSING_STEP,SEQUENCE |
| case_29 | INCOMPLETE | 12 | FIELD,MISSING_STEP,SEQUENCE |
| case_30 | INCOMPLETE | 12 | FIELD,MISSING_STEP,SEQUENCE |
| case_31 | ABSTAIN | 1 | POLICY_CONDITION_NOT_ESTABLISHED |
| case_32 | ABSTAIN | 3 | POLICY_CONDITION_NOT_ESTABLISHED |

## I. Full518 blast radius

280 resolved,238 unresolved;88 COMPLETE,182 INCOMPLETE,10 NOT_APPLICABLE.
Unknown-to-resolved:case33 andcase61 (full IDs are case_33 andcase_61).
No resolved-to-unknown transitions; no COMPLETE-to-INCOMPLETE or reverse changes.
25 full-case candidate plans change. Added candidate operations:23 exposed-PII
findings,23 redactions,23 redaction checks,2 remaining-record findings,2 deletes
and2 absence checks. One retained verification citation is replaced, not an
additional retained resource. All counts concern diagnostic candidates unless a
case passes the full gate. Exact changes/citation IDs are in blast_radius.json.

## J. Tests and checkpoint decisions

538 tests pass in24.63s:all503 protected tests plus35 Phase06B controls. The first
19 new controls initially had4 failures and15 passes, demonstrating the actual
missing order-context, multi-source and permission-fact behavior. Positive,
negative, future/expired/cross-copy, alias collision, independent provenance,
opaque-ID, unrelated-evidence, duplication, ordering, timezone and text-format
controls now pass. No prior test was removed, weakened or skipped.

Batch1 ACCEPT:52 support scopes recovered and phantom permission claims removed;
full/public publication unchanged. Batch2 ACCEPT:explicit catalog joins recover
two full cases with no status regressions; published public results unchanged.
Unsupported retention dates, generic ticket contexts and unproven artifact
relationships remain BLOCKED. No feature was accepted solely for filling rows.

## K. Gate assessment

See gate_assessment.json. Exact CSV contract/time/citation rules are official;
identity/condition/corpus completeness are necessary evidence safeguards. The
single-artifact condition requirement was overly strict and corrected with a
concrete counterexample. Joint state-field support remains an internal assurance
check. Claim-only phantom scopes were an implementation defect. Uninterpreted
matching documents still block completeness; already-compliant records are not
rejected merely because they need no remediation.

## L. Release, reproducibility and traces

The final production publication, optimized-Python packaging check and fresh
source reproduction are recorded below when executed. No new release bundle
will be built unless all518 semantic/contract gates pass. The historical
submission remains preserved and uncertified. The active Codex session cannot
have a complete final trace export until it ends; follow agent_trace_instructions
and review relevant Codex/Antigravity traces only, excluding credentials/unrelated
sessions. No external challenge upload or paid model call occurred.

## M. Skills actually applied

hackerrank-orchestrate-evidence:source/fact/provenance maps;
orchestrate-test-fix:before-fail-fix-regression and full blast-radius comparison;
hackerrank-orchestrate-design:architecture-preserving derived availability and
model/code boundaries; orchestrate-submit and hackerrank-orchestrate-package:
independent gates, explicit inventory and blocked-release discipline. No new
skills/frameworks were installed, no agent swarm introduced, no score prediction
or fabricated interview/transcript produced.

## N. Remaining risks and evidence needs

Highest impact:missing retention intervals on202 requests. Next:75 ambiguous or
unestablished support-context scopes, unlinked absent/deidentified resources,
three exclusive-ownership andthree archive-existence gaps, one undated hold,
and ordinary documents whose exact storage relationship remains unestablished.
A model could help interpret supplied text only with approved configuration and
budget; it cannot supply missing dates, nulls, ownership or resource IDs.

The official event page advertises24 hours from24 October2026 6 PM IST, implying
a nominal end25 October6 PM IST. The authenticated contest-specific cutoff was
not verified. Source:[HackerRank timetable](https://www.hackerrank.com/hackerrank-orchestrate-october26).
No ranking or hidden accuracy is claimed.

## O. Verdict

NOT READY — CRITICAL BLOCKERS REMAIN

## Final source-interpretation checkpoint

The continued Attachment properties and upload history section of evidence_58
was inspected in full. Together with the literal internal support reference and
file-properties field it establishes support_001 as an attachment record. This
recovers identity/type/presence only; a single customer uploader does not establish
sole ownership. Case07 therefore remains UNKNOWN at its policy condition, not
simply at raw document capture. The explicit catalog for object_19 does not lend
exclusivity to this different support resource. No deletion of the form is added.
The 536- and 537-test checkpoints were followed by the form-properties and
nested-quotation controls; the final suite has 538 passes in 24.63s. Current full statuses and proof fingerprint are unchanged
from the preceding batch:280 resolved,238 unknown.

The matrix generator encountered a local-variable shadowing error after adding
condition-outcome reporting. It was corrected and the complete generator reran
successfully. This did not alter inference rules; all final matrices include the
actual TRUE/FALSE/UNKNOWN outcome and source references.

Two fresh seeded production reports are identical, exit3 and preserve the older
root CSV. The reference and cached full proofs match. Optimized Python packaging
check exits1 with PACKAGE BLOCKED for238 cases; no new archive is built. The
explicit prospective inventory contains103 members and passes the configured
path/secret-pattern checks. These checks do not certify arbitrary secret absence.
Final clean-source reproduction and checkpoint hashes are recorded below after
the committed-source run. No historical bundle or provided evidence was changed.
