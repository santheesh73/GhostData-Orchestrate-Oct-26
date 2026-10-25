# GHOSTTRACE Phase 06 evaluation report

## Result and readiness

Phase 06 implements real public-sample evaluation, guard-based failure analysis,
feature counts, privacy-limited traces, metamorphic controls and measured identity
optimization. **The application is not submission ready.** All 32 public sample
cases abstain, so published status, exact-row, field and sequence accuracy are 0%.
The full 518-request diagnostic still has 10 NOT_APPLICABLE and 508 unresolved.
No production output.csv, code.zip or submission folder was generated. Phase 07
freeze and submission have not started.

The public reference has 10 COMPLETE and 22 INCOMPLETE cases, 193 steps and no
NOT_APPLICABLE cases. Labels were already inspected in earlier phases: this is
an explicitly labeled development comparison, not a held-out accuracy estimate.
No organizer-only data or hidden answers were read. Hidden/full-dataset accuracy,
identity accuracy, OCR accuracy and semantic extraction recall remain unmeasured.

## Reproducible commands and boundary

```text
python -B code/evaluation/main.py --audit-samples
python -B code/evaluation/main.py --audit-samples --with-extraction --cache-dir .ghosttrace/phase05-verify
python -B code/evaluation/main.py --trace-case case_29 --with-extraction --cache-dir .ghosttrace/phase05-verify
python -B code/evaluation/main.py --benchmark-audits --requests dataset/deletion_requests.csv --repetitions 3
python -B -m pytest -q -p no:cacheprovider code/tests
```

The evaluator loads requests, runs every audit and publication gate, and only
then opens the public expected output. Runtime modules cannot import evaluation
or sample-label utilities. A regression checks the actual ordering of all 32
audits/gates before label access. Trace and benchmark never open labels. These
commands emit JSON to stdout, make zero provider calls, and never invoke a CSV
writer. Raw diagnostic files and extraction caches remain ignored under
.ghosttrace/. The independent publication validator rejects the empty result
for CASE_COVERAGE. Public evaluation correctly exits 1 for imperfect agreement;
input/contract/proof errors exit 2. Successful traces/benchmarks exit 0.

Initial harness correction: a citation catalog built only from parsed observations
omitted valid IDs for deferred PDFs/images. Evaluation now uses the participant
manifest/activity/audit metadata catalog. Citation existence/time eligibility is
separate from successful extraction and semantic support; the reference validates
without declaring deferred contents understood.

## Measured baseline and two configurations

The before measurement used unchanged Phase 05 runtime cb9e142. The after runtime
adds general request grammar fixes and an identity cache, without changing any
publication premise. Structured-only and locally extraction-augmented modes were
both executed before and after; each pair has identical semantic outcomes.

| Measurement | Phase 05 baseline | Phase 06 after |
|---|---:|---:|
| Native authorization agreement | 18/32 (56.25%) | 27/32 (84.375%) |
| Publishable sample rows / abstentions | 0 / 32 | 0 / 32 |
| Status / exact-row accuracy | 0% / 0% | 0% / 0% |
| Published step true positives / reference steps | 0/193 | 0/193 |
| Published step precision / recall / F1 | undefined / 0 / 0 | undefined / 0 / 0 |
| Published correct fields / compared fields | 0/1,351 | 0/1,351 |
| Published exact sequences | 0/32 | 0/32 |
| Unpublishable candidate step overlap | 9/193 | 9/193 |
| Candidate precision / recall / F1 | 1.0 / 0.046632 / 0.089109 | same |
| Candidate correct fields / sequences | 56/1,351 / 0/32 | same |
| Native resolved request authorizations | 18 | 27 |
| Resource-scope assessments | 3 violations, 71 unknown | 3 violations, 95 unknown |
| Structured parse inventory | 79 parsed, 15 deferred | same |
| Augmented capture inventory | 94 parsed | same |

Missing rows count against the 32-reference denominator. Step overlap is a
multiset over six non-number fields; field alignment also compares numbering.
Sequence equality preserves every field and array order. An undefined precision
is null, not 100%. Candidate metrics have the explicit scope
UNPUBLISHABLE_CANDIDATE_STEPS; they never count as predictions or case accuracy.
All nine candidates belong to one still-unresolved development case. The increase
in unknown assessments reflects more requests reaching reconstruction, not a
regression established by ground-truth resource labels.

Generalized authorization fixes cover ongoing erasure language, explicit permanent
closure, continuation of a scoped deletion, quoted benign UI labels, residual
search/export/contact requests in account context, and verification after the
person states they deleted their own account. Nearby negatives cover export/reset,
status-only questions, a deleted filter rather than account, third-party accounts,
quoted erasure instructions and negation. Native authorization rules contain no
case IDs or complete sample sentences and do not read workflow statuses or public
expected labels.
Five public authorizations remain unresolved. They are retained as failures rather
than translated or inferred from their expected answer.

## Failure taxonomy and observed feature coverage

Guard stages overlap; they identify observed blockers, not an asserted causal
model misread. All actual model-call counts are zero. In skill terminology the
known native coverage/interpretation limitations are RULE failures; no MISREAD
classification is claimed without evidence of a model extraction error.

| Guard stage | Baseline cases | After cases |
|---|---:|---:|
| Authorization | 14 | 5 |
| Identity/time qualification | 16 | 25 |
| Retrieval/resource linkage | 16 | 25 |
| Evidence completeness | 18 | 27 |
| Policy/interpretation | 2 | 2 |
| Publication gate | 32 | 32 |

After native interpretation, 25 requests have only snapshot-context identity with
unknown availability, 21 have unestablished resource links and 4 have no assessed
resource. Two cases have unknown policy conditions; one also has unmapped
categories. Context/coverage cannot be promoted just because all files were read.
The three positive scopes are ANALYTICS_PROFILE, DATA_FLOW and SEARCH_INDEX_ENTRY,
each violating; two SUPPORT_MESSAGE scopes and 93 unclassified scopes are unknown.
Nine candidate operation kinds appear, once each: three findings, three remedies
and three verifications. This is observed feature coverage, not exhaustive recall.

The augmented configuration captures 15 additional files but changes no public
semantic result. Fourteen documents remain candidate text; the single anchored
record has partial interpretation. Extraction's marginal end-to-end improvement
in this zero-model configuration is therefore **zero**. Native-only capture and
optional model support must not be confused with a working full audit.

## Case-level golden diff

Every actual status is unresolved and every published row is missing. The table
lists expected public status, candidate/reference step counts and explicit guard
stages: A authorization, C coverage, I identity, R retrieval/linkage, P policy,
G publication gate. Candidate counts are diagnostic only.

| Case | Public expected status | Candidate/reference steps | Blockers |
|---|---|---:|---|
| case_01 | COMPLETE | 0/1 | C, I, G, R |
| case_02 | COMPLETE | 0/1 | C, I, G, R |
| case_03 | COMPLETE | 0/3 | C, I, G, R |
| case_04 | COMPLETE | 0/2 | C, I, G, R |
| case_05 | INCOMPLETE | 0/3 | C, I, G, R |
| case_06 | INCOMPLETE | 0/4 | C, I, G, R |
| case_07 | INCOMPLETE | 0/4 | C, I, G, R |
| case_08 | INCOMPLETE | 0/4 | C, I, G, R |
| case_09 | INCOMPLETE | 0/5 | C, I, G, R |
| case_10 | INCOMPLETE | 0/4 | C, P, G |
| case_11 | INCOMPLETE | 0/14 | C, I, G, R |
| case_12 | INCOMPLETE | 0/5 | A, G |
| case_13 | INCOMPLETE | 0/8 | C, I, G, R |
| case_14 | INCOMPLETE | 0/5 | A, G |
| case_15 | INCOMPLETE | 0/5 | C, I, G, R |
| case_16 | INCOMPLETE | 0/7 | C, I, G, R |
| case_17 | INCOMPLETE | 0/5 | C, I, G, R |
| case_18 | INCOMPLETE | 0/14 | C, I, G, R |
| case_19 | INCOMPLETE | 0/8 | C, I, G, R |
| case_20 | INCOMPLETE | 0/8 | C, I, G, R |
| case_21 | COMPLETE | 0/3 | C, I, G, R |
| case_22 | INCOMPLETE | 0/8 | C, I, G, R |
| case_23 | INCOMPLETE | 0/8 | C, I, G, R |
| case_24 | INCOMPLETE | 0/7 | C, I, G, R |
| case_25 | COMPLETE | 0/3 | A, G |
| case_26 | COMPLETE | 0/6 | A, G |
| case_27 | COMPLETE | 0/6 | C, I, G, R |
| case_28 | COMPLETE | 0/6 | C, I, G, R |
| case_29 | INCOMPLETE | 9/14 | C, P, G |
| case_30 | INCOMPLETE | 0/14 | A, G |
| case_31 | COMPLETE | 0/3 | C, I, G, R |
| case_32 | INCOMPLETE | 0/5 | C, I, G, R |

## One actual input trace

`--trace-case case_29 --with-extraction` validates the request schema, recognizes
explicit deletion, and resolves one subject. It retrieves 4 logical links across
8 state scopes, retaining 9 eligible timeline observations from evidence_92 and
activity_3541 through activity_3544; it excludes 5 future observations and 1 with
unknown time. Three scopes establish analytics identifiers, an active connector
and a search record requiring treatment. Four activity-only scopes have no mapped
category; the support scope lacks its required policy condition. Nine candidate
steps follow, but unknown policy/coverage premises keep the status unresolved.
The writer is never called. Trace output omits request text and direct subject
identifiers; model calls are zero. This is an actual pipeline trace, not a
fabricated successful inference or use of future facts.

## Regression and additional participant cases

Full observed command: **384 passed in 12.12 seconds**, including the 340 existing
checks and 44 Phase 06 tests. Controls use handwritten fixtures, not public answer
rows. Three additional classes exercised here are:

1. Authorization minimal pairs: 11 new positives and 12 neighboring negatives,
   including harmless UI quotations versus embedded commands and account history
   versus deleting a saved filter. Review restored the informational-question
   guard for “explain when” and “what ... can you delete”; both have counterexamples.
   Existing negation/language tests still pass.
2. Shared/reassigned identity: reference and optimized reconstructions agree at
   six cutoffs, including exact reassignment boundaries, a future-only registry
   entry and an early reference that cannot borrow that later registry. A later
   view warmed first cannot promote an undated snapshot in an earlier view.
3. Policy metamorphisms: three arbitrary subject/resource/case naming schemes,
   reversed input order, equivalent timezone offsets and future absent-state
   noise preserve the independently asserted INCOMPLETE plan and exact citation.

The fingerprint test deliberately drops an unpublished candidate plan and detects
it even though the final unresolved decision is unchanged. A deliberately broken
benchmark implementation raises a proof mismatch rather than reporting a speedup.
Other controls reject invalid trial counts/cache escapes/unknown trace IDs,
separate candidate/status metrics, retain trace privacy and check inference-label
import isolation. Earlier independent COMPLETE, INCOMPLETE and NOT_APPLICABLE
synthetic roundtrips, protected retention/tombstones, multi-copy conflicts,
canonical ordering, source eligibility, writer preservation and real local OCR
checks remain passing. Synthetic success does not establish public accuracy.

## Measured optimization

A real pre-change cProfile trace of the 32-sample audit attributed 0.817 cumulative
seconds to 18 IdentityGraph.at calls, the dominant processing hotspot. Profiling
has overhead and is not used as the speed benchmark.

Only fixed-input work is cached: normalized immutable snapshot candidates, their
alias/subject indexes, and exact stable-reference pairs when the eligible subject
registry is unchanged. Snapshot candidates retain certain=false and missing
availability. Audit history, time qualification, conflicts and resource replay
remain cutoff-specific. Future registry entries force the original pairing path.
There is no global cross-dataset or cached-cutoff result reuse. The uncached path
is retained as an explicit development reference.

Final benchmark: CPython 3.14.3 on this Windows machine; 518 requests, one common
untimed warm-up, three trials per configuration with alternating order. Ingestion,
startup, label I/O and fingerprint serialization are excluded. No test suite ran
concurrently with this final measurement. The earlier exploratory run overlapped
regression work and is not the reported timing. Peak memory was not measured.
The final repeat after restoring informational-question guards is reported below;
the earlier serial repeat was 1.97×. Local load varied, so the latest observed
ranges accompany the medians rather than selecting the faster result.

| Configuration | Median engine seconds | Median audit seconds | Median processing seconds | Processing range |
|---|---:|---:|---:|---:|
| Uncached reference | 0.346039 | 12.482549 | 12.872485 | 12.720762–14.212807 |
| Cached immutable context | 0.341569 | 6.458603 | 6.816385 | 4.499196–7.250012 |

Median processing speedup: **1.8885×** (47.05% less time) for this local workload.
All six complete audit fingerprints, including candidate plans and all proofs,
match the warm-up. This is a measured processing improvement, not an end-to-end
accuracy improvement or universal speed guarantee. No dependency was installed.

## Full-run repeatability, cost and provenance

Two fresh extraction-augmented full runs with PYTHONHASHSEED=0 and 12345 produce
identical entire JSON diagnostics, both exit 3: 484 DELETION authorizations,
10 NON_DELETION, 24 UNRESOLVED; 10 NOT_APPLICABLE, 508 unresolved final cases;
134 violating, 42 compliant and 1,770 unknown scope assessments. The full diagnostic
proof also equals Phase 05. Each run makes zero provider calls/tokens and has USD0
model-service cost. This excludes Codex development usage and local compute.
No output-producing full run or final usage report exists.

| Bound measurement | SHA-256 |
|---|---|
| Public requests | b3802bdb242ab4869d84191a6c0d3f7d1601afbc6114833f9184c323d319c7e6 |
| Public expected output | 72ef6b14f504a72a674deefad08c66e397f8d8c05bd23d9791e41db6ef184d91 |
| Evidence/context file bytes and paths | f5049da0e32fc967628fc6f597a0e79434cf74c72da5962d791c974a0c158d43 |
| Manifest file | bcb1d0b909dfe2b29dd461f9d7e90d8a031803de21858d5f18f52c771ab0d614 |
| Supplied rules | 17332f5566e776d2f7bcff36e93cf23c9d8594dc2ff1e9c247ad2614539dc40f |
| Runtime implementation after | 558f08aa0267f57755b59ad47508e94d014abd8d7e1ced03539543a03b558f8f |
| Sample semantic result, both modes | 9d7bce4c978fdb1ab35b095de0a529820056f75d7a52a337cbb86eef0cf479b7 |
| Full benchmark complete-audit fingerprint | e61502c6e6ade0f1a058aaa57f3a4071c96bad96d36cc4ccbce7620fda28344b |
| Full augmented diagnostic proof | c85b1c97969dca93f4c684aa77b1eccd19fd3d374dfae68f06cef408e802be22 |

The runtime fingerprint hashes runtime Python/PowerShell/prompt text by relative
path and bytes; diagnostics also record source, request, manifest and rule hashes.
The corpus digest alone covers file bytes/paths; the separately bound manifest
supplies source clocks/origins. Raw artifacts stay private under .ghosttrace/;
these Markdown results and genuine commands/logs are the reviewable evidence.
No causal skill-effectiveness experiment or official score estimate was run.

## Remaining failures and next gate

Phase 06's evaluation/optimization work is implemented. Its accuracy/readiness
gate **fails**. Time-qualified identity/alias evidence, semantic document and
conditional-policy coverage, remaining authorization interpretation and exhaustive
copy/flow accounting require additional work before freeze. Increasing parse
counts or asserting coverage_complete would conceal these failures. Phase 07
packaging/release remains unstarted; no submission readiness claim is made.

---

# Archived Phase 05 evaluation report

## Measured implementation gate

Phase 05 adds optional PDF/image capture, literal record extraction, a selective
model seam for unresolved content/intent, source-bound caches, bounded retries
and genuine usage accounting. It does not run Phase 06 optimization or create
predictions/submission artifacts. The historical phase reports below retain
their original scope and measurements.

Final command: `python -B -m pytest -q -p no:cacheprovider code/tests`.
**340 passed in 8.70 seconds**, retaining the 285 earlier regressions and adding 55
extraction/provider/cache/usage checks. Actual native Windows OCR and PDF reading
are exercised; provider integration uses test doubles, not paid/live calls.

## Actual capture and audit diagnostics

Commands:

```text
python -B code/main.py --extract-evidence --cache-dir .ghosttrace/phase05-verify
python -B code/main.py --audit-policy --with-extraction --cache-dir .ghosttrace/phase05-verify
```

| Measurement | Actual result | Scope |
|---|---:|---|
| Previously deferred files read | 15/15 | 4 PDFs and 11 PNGs |
| PDF pages / image pages | 7 / 11 | All 18 pages accounted for |
| Captured text units | 992 | Blocks/lines with locations, source hashes and boxes |
| Literal anchored record observations | 1 | Partial semantic coverage, not a complete case |
| Indexed observations after augmentation | 10,729 | Previous 9,736 plus 992 text units and 1 record |
| Extraction source failures / unreadable pages | 0 / 0 | Actual successful local run |
| Native policy authorizations | 484 DELETION, 10 NON_DELETION, 24 UNRESOLVED | Same as Phase 04 |
| Full case outcomes | 10 NOT_APPLICABLE, 508 unresolved | No publishable real deletion answer |
| Resource-scope assessments | 134 violating, 42 compliant, 1,770 unknown | Coverage counts, not accuracy |
| Provider calls / input / output tokens | 0 / 0 / 0 | No provider configured; default call budget zero |
| Model service cost | USD 0 | Excludes Codex development usage/local compute |

PARSED on these files means supported text capture completed. It does not mean
all business semantics were extracted. Fourteen documents yield candidate text
without a promoted record; the one record also remains only partially interpreted.
There are 14 document-model tasks plus 24 unresolved request tasks, reported as
38 MODEL_NOT_CONFIGURED events. No model was invoked for the ordinary supported
requests. The source availability and exhaustive coverage gates stay in place.

No challenge identity/deletion/step/field/sequence accuracy, semantic extraction
recall, OCR character accuracy, hidden score or ranking is measured. Capturing
all files does not establish coverage_complete. No public answer labels enter
the extraction path.

## Validation and independent controls

- Real local OCR reads a handwritten synthetic image; a blank image fails instead
  of generating absence/null/disabled evidence. Swapped-source quotes are rejected.
- Actual two-page PDF extraction accounts for both pages and preserves the source
  bytes. Magic mismatches, pixel/text/page bounds and incomplete pages are checked.
- Handwritten record fixtures verify opaque resource anchors, literal field/quote
  binding, false versus zero, null versus missing, exact locators and schema keys.
  Fabricated values, other-system targets, output verdicts, wrong labels and
  malformed/duplicate fields are rejected.
- Cache tests bind bytes, origin, path and capture time; corrupt entries and
  path traversal are rejected. Replay repeats grounding validation rather than
  trusting valid JSON. Source files changing during extraction fail explicitly.
- Model tests cover strict Responses schema, returned model/tokens, sanitized
  transport errors, refusals/permanent failures, transient retries, invalid JSON,
  zero/cross-job budgets, oversized inputs and missing providers.
- Usage checks retain every build retry in cached provenance, distinguish current
  from replay/build usage, preserve unknown billing, reject invalid rates, and
  correctly apply an explicitly zero cached-input rate. Cache-write failure does
  not double count a successful call.
- Intent fixtures preserve negation and require an original quote. Supported
  requests avoid calls; duplicate unresolved text reuses one result. The
  unsupported-language route also blocks quoted/instruction-override requests.
- Injected model outputs are consumed through both evidence and policy seams,
  proving the optional adapter is connected. These are mocked integration tests,
  not measured translation/model accuracy.
- Extraction metadata cannot become business PII or identity. Existing policy,
  retention, temporal, emission, independent CSV and output-preservation checks
  remain passing. Diagnostics do not modify an existing prediction.

## Observed failures and corrections

PowerShell 7 could not expose the Windows Runtime OCR types. The verified local
adapter uses Windows PowerShell 5.1 with existing en-US recognition, passing a
fixed reviewed program and a separate path argument. It changes no execution
policy/profile and installs no language pack. The initial sandbox run blocked
OCR temporary image snapshots; the authorized temporary-directory run succeeded
on all 11 images. Cached replay needs no new OCR snapshots.

Review reserved extraction-proof metadata from business-field walkers, bound
field labels as well as values, retained failed/rejected model attempts in cache
build accounting, and closed a quoted-request guard on the non-Latin route.
These changes have regression fixtures. They are engineering corrections, not
a measured improvement in challenge-answer accuracy.

Dependencies already present: PyMuPDF 1.27.2.3, Pillow 12.2.0 and native Windows
OCR. No dependency installation or live provider request occurred. The optional
extras file records the tested Python versions. Tesseract fallback on another OS
and hosted-model/account compatibility were not verified live in this environment.

## Reproducibility and timing limits

Cold extraction: 15 cache misses, 0 hits, **7.5361 seconds** observed command wall
time. Warm extraction: 15 hits, 0 misses, **2.0275 seconds**. Both capture 992 units
and 1 anchored record with no errors. These are single observations including
startup, not a statistical benchmark or a general performance claim.

Two fresh processes used PYTHONHASHSEED=0 and 12345 for cached full audits from
outside the repository. Entire parsed reports matched, including every case
outcome, source-derived proof and usage counters. Observed times were **10.2421**
and **10.3324 seconds**; both exited 3 for unresolved cases.

Aggregate proof SHA-256:
`c85b1c97969dca93f4c684aa77b1eccd19fd3d374dfae68f06cef408e802be22`.

This establishes fixed-input cached replay repeatability. It does not establish
fresh OCR/model bit stability or correctness of business claims. Cache digests
detect source mixups/corruption, not malicious rewriting of both data and digest.

## Remaining work and applied guidance

The optional model path is implemented and mock-tested but not verified with a
live configured provider. All 24 unresolved-language requests and broader document
interpretation remain pending. Exhaustive coverage, provisional identities,
unknown policy conditions/categories and retained-state proof still block the
508 unresolved cases. A model must not invent source availability or a verdict
to make these counters disappear. Final prediction-run usage remains unavailable.

Applied PDF extraction/visual-review guidance, Orchestrate build/design and
prompt-engineering guidance, multimodal source-grounding controls, and the
[official OpenAI Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs)
for the optional transport. No causal skill-effectiveness experiment was run.
Official instruction files and dataset are unchanged. Stop before Phase 06.

---

# Historical Phase 04 evaluation report

## Current implementation and measured gate

Phase 04 adds authorization, supplied-policy condition evaluation, retention
and tombstone safeguards, residual identifier checks, flow/restore risks,
canonical plan assembly and an audit publication gate. Phase 05 extraction has
not started. No real output.csv or submission archive was generated.

Final test command: `python -B -m pytest -q -p no:cacheprovider code/tests`.
**285 passed in 12.26 seconds**, retaining all 209 earlier regression tests and
adding 76 Phase 04 checks. Runtime uses the standard library; no packages,
providers, services or frameworks were installed. Model calls/tokens were zero.

## Full participant-data audit diagnostics

Command: `python -B code/main.py --audit-policy`.
The final runs used absolute entry-point paths from outside the repository.

| Measurement | Result | Limit |
|---|---:|---|
| Requests processed | 518 | All selected requests accounted for |
| Authorization: DELETION | 484 | Supported deterministic grammar, not measured accuracy |
| Authorization: NON_DELETION | 10 | NOT_APPLICABLE, no deletion operations |
| Authorization: UNRESOLVED | 24 | Unsupported-script requests defer to later interpretation |
| Resolved public decisions | 10 | All NOT_APPLICABLE |
| Unresolved public decisions | 508 | Includes the 24 unresolved intents |
| Violating resource-scope assessments | 134 | Supported local findings; not complete case plans |
| Compliant resource-scope assessments | 42 | Scoped treatment only; not case-level completeness |
| Unknown resource-scope assessments | 1,769 | Includes provisional ownership and unsupported facts |
| Deferred PDF/PNG files | 15 | Same four PDFs and eleven PNGs as Phase 02 |
| Ingestion errors / isolated case exceptions | 0 / 0 | No source or case-processing failure in these runs |
| Root prediction written | No | Publication remains blocked by unresolved cases |

Overlapping case uncertainty counts: 484 lack established exhaustive evidence
coverage; 385 lack time-qualified request identity; 384 contain provisional or
ambiguous resource links; 58 contain an unsupported/unestablished policy
condition; 53 contain unmapped categories; five lack a required retained-record
state; four have unknown flow state; one lacks a record state and one has no
assessed resources. Unsupported-script intents account for 24 cases. These are
engineering diagnostics, not gold-label error counts.

CLI exit 3 correctly reports unresolved cases. The no-argument runner remains
a lightweight, non-publishing diagnostic with POLICY_AUDIT_NOT_RUN; it is not the
full policy execution. File parse success and candidate retrieval never assert
exhaustive subject coverage. The runtime does not set coverage_complete=True.

## Independent synthetic validation

All expected outcomes below are handwritten in code/tests/test_policy.py,
independent of public reference outputs. The policy tests exercise all 15 allowed
operations across their fixtures. Full challenge status/step/field/sequence
accuracy remains NOT_MEASURED; no hidden accuracy or score is estimated.

| Custom case | Expected and observed result |
|---|---|
| Present profile with an authorized deletion | INCOMPLETE: cited remaining-record finding, DELETE, future absence check |
| Later absence readback plus asserted exhaustive synthetic scope | COMPLETE: cited absence verification only |
| Export/correction/marketing-only or negated request | NOT_APPLICABLE: empty operations; no identity prerequisite |
| Shared support conversation | REDACT the subject identifiers, preserve the conversation and agent fields |
| Subject-only attachment / unproven ownership | DELETE only when sole-subject condition is established |
| Analytics retains a stable user reference | ANONYMIZE even when direct email/phone/hash fields are cleared |
| Proper tombstone / extra direct identifier | Preserve stable reference; redact any remaining direct identifier |
| Retention/hold in force / missing retained record | VERIFY_RECORD_PRESENT / unresolved; never DELETE |
| Active connector / disabled connector | Disable before destructive changes / evidence-backed disabled check |
| Restore-permitted backup | Retain archive, BLOCK_RESTORE and verify retained presence plus restore block |
| Primary absent, replica present | Keep the replica violation and its evidence |
| Conflicting per-copy policies or canonical dependency order | Unresolved; no destructive public decision |

The three-case policy roundtrip writes only a temporary synthetic CSV and
checks COMPLETE, INCOMPLETE and NOT_APPLICABLE against exact expected steps,
states, citations, phases, numbering and resource targets: **3/3 exact cases,
4/4 steps and 28/28 public fields checked**. Publication passes the audit proof
gate, existing emitter, independent structural validator and atomic writer.
Exhaustive coverage is an explicit synthetic premise, not a real-data claim.

Negative controls cover quoted/hypothetical/embedded instructions, conflicting
authorization, retention exceptions, unsupported languages, historical subject
proof, future observations, reported workflow status changes, unknown conditions,
false shared/sole ownership conditions, unknown/expired retention, attribution
through stable references, omitted fields, unparsed narrative, nested/additional
identifier values, conjunctive citation coverage, SQLite versus JSON Boolean
types, malformed scheduler flags, copy preservation, safe operation order,
tampered citation/action/resource, missing coverage, source-proof gates, preserved
existing output, isolated case failures and the diagnostics-only CLI.

## Corrections found during review

The initial full run classified two affirmative deletion requests as non-deletion:
the grammar missed “would like it permanently deleted”, then interpreted “correct
treatment” as a correction action. A generic request-cue fix, unscoped-mention
guard and regression examples corrected this. Limited Spanish/French grammar
was added; unsupported scripts explicitly defer rather than taking a fallback
status. This was a concrete observed classifier error, not a measured change in
full challenge accuracy.

Review also added nested/additional identifier checks for tombstones, ensured
malformed optional controls stay unknown, kept complete verification from citing
an artifact that proves only one conjunct, and independently protected retained
categories in the audit gate. One development test failed because its harness
double-decoded the validator's already parsed steps_json; fixing that test reader
resolved it without changing production output logic. Final suite: 285 passing.

## Determinism and timing

Final fresh-process runs with PYTHONHASHSEED=0 and 12345 produced identical
entire parsed reports. Runtimes, including process startup, were **18.0942** and
**18.0825 seconds**. These are individual observations, not a benchmark or speedup.

Aggregate proof SHA-256:
`a74831053403d2cfd2351cd72ee6f1e7d27a8f9d6c413a7fb29a77821210b211`.

The fingerprint binds source hashes (including policy CSV), decisions, assessed
operations and proof IDs without printing request text or identifiers. The
repeatability claim covers these fixed input bytes/metadata and current offline
adapters. It does not claim provider determinism or robustness to changed facts.
Observation-order and future-evidence controls are retained in the tests.

## Limits and next phase

- Ten non-deletion decisions resolve; no real deletion case has a publishable full
  answer yet. Local findings are retained for subsequent work.
- Twenty-four unsupported-language requests, 15 deferred files, provisional
  identities, unmapped schemas and unsupported conditions still need evidence or
  interpretation. A model must not invent snapshot availability timestamps.
- Exact supported text/field matches can prove exposure; absence of a match in
  unsupported narrative cannot prove redaction. Current grammar is deliberately
  narrower than general multilingual understanding.
- The audit gate verifies proof/assembly/clock/retention consistency; it does not
  independently reimplement every policy predicate. The original CSV validator
  remains an independent structural boundary. Semantic correctness is tested on
  synthetic cases and remains unmeasured on challenge labels.
- Exhaustive coverage requires additional engineering evidence. No override was
  used to publish provisional real decisions, and final-run usage is unavailable.

Applied orchestrate-build guidance for typed boundaries and isolated failures;
hackerrank-orchestrate-design for explicit unknowns, evidence-backed claims and
exclusive emission. No causal skill-effectiveness experiment was performed.
Official dataset and instruction files remain unchanged. Stop before Phase 05.

---

# Historical Phase 03 evaluation report

## Current phase and measured gate

Phase 03 implements historical identifier ownership, account/resource links,
audit-cutoff replay, and explicit conflicts. It makes no policy/risk decision and
produces no real prediction CSV. Runtime never reads sample_output.csv or private
labels. The historical Phase 01/02 reports below retain their original scope.

Final command: `python -B -m pytest -q -p no:cacheprovider code/tests`.
**209 passed in 12.35 seconds**, retaining all 149 Phase 01/02 regression tests
and adding 60 Phase 03 checks. Windows, CPython 3.14.3, existing pytest 9.1.1;
no dependencies installed and no runtime model calls.

## Full participant-data reconstruction diagnostics

Command: `python -B code/main.py --reconstruct-evidence`.
Both final executions processed all 518 requests, exited 0, and reported no
ingestion errors. The CLI was invoked by absolute path from outside the repo.

| Measurement | Observed result | Interpretation |
|---|---:|---|
| Requests processed | 518 | Every selected request has diagnostics |
| RESOLVED subject identities | 101 | Time-qualified identity evidence, not labeled accuracy |
| CONTEXT_ONLY subject candidates | 417 | Snapshot availability unknown; kept provisional |
| LINKED resource associations | 680 | Grounded to a candidate subject, independently of request identity certainty |
| PROVISIONAL resource associations | 523 | Context/catalog linkage requires corroboration |
| Source-specific copy/instance state scopes | 2,046 | Includes claim-only scopes; not proven distinct storage replicas |
| Cases with STATE_NOT_ESTABLISHED | 285 | At least one scope has claims without a recognized readback |
| Cases with provisional resource links | 258 | May overlap other uncertainty counts |
| Cases with no linked resources | 10 | Does not establish absence |
| Equal-time conflicting extracted dimensions | 0 | Supported adapters/scopes only; does not prove all evidence agrees |
| Deferred PDF/PNG evidence | 15 | Four PDFs and eleven PNGs still require Phase 05 |
| Root output.csv written | No | All production decisions remain unresolved |

The same Phase 02 corpus has 9,736 observations from 94 manifest files and four
context CSVs. Counts above are engineering coverage, not correctness metrics.
No challenge identity, temporal-state, retrieval, deletion-status, step, field,
sequence or hidden-case prediction accuracy has been measured in Phase 03.
Existing Phase 01 synthetic compiler metrics below remain synthetic only.

## Independent synthetic cases and actual results

The expected outcomes are handwritten under code/tests; none comes from public
reference labels. Each listed behavior passed its dedicated regression check.

| Custom case | Expected | Actual |
|---|---|---|
| Shared email leaves A and joins B at day 10 | Request on day 9 resolves A; day 10 resolves B; no union | PASS |
| Old email after retirement, unique owner | Recover the historical subject and older resource links | PASS |
| Claimed DELETE/RESTORE SUCCESS after a positive readback | Preserve observed presence; retain operations as claims | PASS |
| Primary absent, replica still present | Separate scopes preserve both states | PASS |
| SQL and JSON disagree at the same time/copy | Unknown with both values and all proof IDs | PASS |
| File captured after cutoff, earlier internal timestamp | Exclude it; existing proof fingerprint unchanged | PASS |
| Later snapshot omits email | Unknown field; distinct from explicit null/redaction | PASS |
| Reused trace in another file/service/instance | No subject propagation | PASS |
| Later identity registry event | Cannot reinterpret an earlier reference before cutoff | PASS |
| Envelope user with unrelated nested sender email | No cross-object alias ownership | PASS |

Additional controls cover half-open interval boundaries, both endpoint proofs,
broken/duplicate/equal-time history, current snapshot uncertainty, phone/hash
normalization, opaque subject/resource/case IDs, input order, same resource ID
across systems, stale aliases after reassignment, causal trace direction,
catalog-link claims, unknown clocks, null-versus-unknown, malformed Boolean/count
facts, bounded long numeric counts, scoped query absence, conflicting query
counts/documents, later recreation, and CLI preservation of an existing output.

## Reproducibility and timing boundary

Two fresh processes used PYTHONHASHSEED=0 and PYTHONHASHSEED=12345. Their entire
parsed diagnostic reports matched, including every case's proof fingerprint.
Observed runtimes including Python startup: **18.9388** and **21.2317 seconds**.
These are individual observations, not statistical benchmarks or speedup claims.
The test suite also retains a small cross-process/hash-seed regression.

Aggregate proof SHA-256:
`a20a38e5f79b5d464c8886d5e1080f527163aabb6b3bbf9114d32d31f8d90116`.

This guarantee covers offline replay of these fixed input bytes/metadata and
the current adapters. Provenance hashes deliberately change when source bytes
or manifest metadata change. Reversing observation input order does not change
proofs; changing source file row order changes provenance even when semantics
remain the same. No hosted model/provider determinism is claimed.

## Review corrections and alternatives

The first implemented ownership/replay suite passed 202 tests. Review then added
controls for interval endpoint provenance, stopped-query ownership, current-field
omission, alias assignment leaking backwards, unrelated nested aliases, future
registry interpretation, cross-process determinism, and long numeric counts.
Resource links now retain ownership and trace proof IDs as well as record IDs.
The final suite passed 209 tests; these are review improvements, not measured
before/after challenge-answer improvements.

Unconditional alias union was rejected because it merges reassigned addresses.
Latest-operation-wins was rejected because SUCCESS can contradict a direct
readback. Format ranking was rejected because two copies can legitimately differ.
The selected alternatives are temporal ownership, claim-specific readbacks, and
per-copy equal-time conflict preservation. Synthetic counterexamples validate
these mechanisms; no model-strategy A/B run or causal skill experiment was done.

Applied skills: orchestrate-build for typed recovery boundaries;
hackerrank-orchestrate-design for explicit unknowns/output ownership;
orchestrate-test-fix and its coupling/determinism references for counterfactual,
opaque-ID, ordering and fresh-process controls. The current contract overrides
generic skill fallback labels and historical scoring claims.

## Remaining limitations and next gate

- Snapshot identity candidates remain provisional where no eligible time-qualified
  corroboration exists. This affects 417 request-to-subject matches.
- Untyped references, resource aliases, source categories and physical-copy
  equivalence are not inferred from naming conventions. Provisional/catalog
  links and ownership ambiguity must block unsupported decisions.
- Supported readbacks can prove only their explicit resource/copy/time scope.
  Latest observed does not prove continuous coverage to audit_at. Missing lookup
  hits, claim-only scopes and ingestion deferrals cannot establish completeness.
- Fifteen PDF/PNG files remain deferred; unsupported log event names remain
  claims, not direct state. Broader semantic recall is NOT_MEASURED.
- Phase 04 applicability/policy/retention/tombstone/risk decisions, derivation
  validation and remediation planning remain unimplemented. No final output or
  submission artifacts were generated; final-run usage is unavailable.

The default runner exits 3 with 518 unresolved decisions and
POLICY_ENGINE_NOT_IMPLEMENTED. Official dataset and instruction files are
unchanged. Phase 04 requires explicit user approval and has not started.

---

# Historical Phase 02 evaluation report

## Current phase and measured gate

Phase 02 adds structured evidence ingestion, exact candidate indexing, source
provenance, and per-file parsing diagnostics. It does not resolve historical
identity, reconstruct final state, evaluate policy, or produce predictions.

Final command: `python -B -m pytest -q -p no:cacheprovider code/tests`.
**149 passed in 11.21 seconds**, including the 89 Phase 01 regression tests.
Environment: Windows, CPython 3.14.3, existing pytest 9.1.1, SQLite 3.50.4.
No packages were installed and no model calls were made.

## Actual corpus coverage

| Source | Files | Normalized observations | Status |
|---|---:|---:|---|
| JSON evidence | 28 | 1,182 | PARSED |
| SQL evidence | 24 | 1,120 | PARSED |
| Log evidence | 26 | 2,211 | PARSED |
| Handover text | 1 | 41 | PARSED |
| PDF evidence | 4 | 0 | DEFERRED to Phase 05 |
| PNG evidence | 11 | 0 | DEFERRED to Phase 05 |
| Identity/audit/activity/policy CSV context | 4 | 5,182 | PARSED |
| Total manifest evidence | 94 | 4,554 | Every file accounted for |
| Total indexed observations including context | — | 9,736 | No ingestion errors |

Structured file parse rate is **79/79**. This measures supported syntax/adapter
accounting, not evidence recall, correct subject association, state reconstruction,
or deletion accuracy. Metadata scopes, raw events, and operational claims are
included in observation totals; they are not 9,736 established business facts.
The 15 document/image deferrals are reported individually, never hidden as success.

Each actual source hash was compared with the current file bytes in tests. Source
locators, nested capture clocks, copy/table identities, and raw payloads survive
normalization. CSV context excludes requests and all public output labels.

## New extraction and negative-control tests

- Independent synthetic JSON snapshots and nested service exports verify resource
  extraction, null/false/empty preservation, nested locations, and separate clocks.
- All six log envelope families are exercised. Trace expansion preserves separate
  payloads and rejects cross-service/instance linkage. Conflicting headers/payloads
  remain diagnosed. Unknown narrative/events remain unparsed observations.
- SQL tests preserve primary/replica differences, embedded JSON, apostrophes and
  semicolons, declared indexes, and capture metadata. Unsafe attachment, vacuum,
  pragmas, extensions, triggers, virtual tables, arbitrary function execution,
  and incomplete/uncommitted snapshot transactions
  are rejected without creating the test's external database file.
- Malformed embedded JSON and incorrectly typed SQL resource identifiers remain
  raw/unparsed with explicit diagnostics.
- Generic evidence CSV tests preserve strings and account for ragged records.
- Retrieval tests cover exact identifier normalization, idempotent indexing,
  separate source locations/copies, source-metadata binding, inclusive cutoff,
  future capture/event exclusions, and unknown-time counters. No-hit retrieval
  never establishes absence.
- Path traversal and non-evidence namespace paths are rejected. Missing/malformed
  sources do not hide good files. Empty manifests fail; cross-source ID collisions
  prevent clean coverage. Identity/policy context cannot become permitted citations.
- Long unbroken text exercises bounded candidate/key scanning without a timing
  threshold or a claimed performance benchmark.
- Actual corpus and CLI tests verify all manifest/context accounting and preserve
  the Phase 01 compiler/comparator behavior.

## Observed failures and corrections

The first development ingestion run parsed 55 files, deferred 15, and rejected all
24 SQL sources: the authorizer rejected primary-key autoindexes. Allowing those
made 68 files parse; the remaining 11 inventory dumps contained explicit CREATE
INDEX statements. Supporting bounded in-memory index DDL resolved that diagnosed
compatibility gap. This was parser improvement, not measured answer improvement.

Further controls preserve envelope contradictions, mark invalid embedded SQL
records unparsed, include malformed sources in coverage denominators, and bind
observation IDs to manifest metadata as well as content. These corrections have
dedicated regression tests; unsupported SQL capabilities remain rejected.

## CLI and determinism observations

| Actual invocation | Exit | Single observed seconds | Result |
|---|---:|---:|---|
| `python code/main.py --ingest-evidence` | 0 | 2.2225 | 94 evidence files + 4 context sources accounted for |
| `python code/evaluation/main.py --ingestion-coverage` | 0 | 2.2803 | 79/79 structured files parsed; 15 deferred |
| `python code/main.py` | 3 | 0.2790 | 518 unresolved; no output written |

Timings include process startup and are single smoke observations, not statistical
benchmarks. Two complete ingestion runs had identical SHA-256 over sorted
observation IDs:
`c88f7fc84e428792d86b0b121312b928bb7e640130984a48b428eb582337bd3e`.
This establishes repeatability for unchanged source bytes/metadata and this
parser configuration, not correct interpretation of every source.

## Remaining metrics and next gate

Identity accuracy, evidence recall, temporal/policy accuracy, status accuracy,
exact-row accuracy, and hidden accuracy remain **NOT MEASURED** for real cases.
No production `output.csv` exists. No full-dataset prediction run or final usage
report can yet be claimed. Peak memory was not measured.

Phase 02 satisfies its structured-source accounting gate. Phase 03 requires user
approval and must preserve contradictions, unknown availability, and copy scope.
No identity resolver or temporal state engine was implemented here.

## Skills

Applied `orchestrate-build` to parser boundaries, bounded failure behavior, and
regression checks; applied `hackerrank-orchestrate-evidence` to byte-bound
provenance, actual observed test results, and separation of parsing from meaning.
No causal claim about skill impact is made. Genuine tool/test evidence remains
in the Codex session trace and the append-only project log.

---

# Archived Phase 01 evaluation report

## Scope and status

Phase 01 implements contracts, request/metadata loading, compilation of supplied
synthetic decisions, independent structural validation, and public-reference
comparison. It does not infer deletion outcomes. Real dataset accuracy and hidden
accuracy are **NOT MEASURED**. No final root `output.csv` was generated.

The approved Phase 00 gate correction is retained: a fixture-backed compiler and
real-input diagnostics precede the evidence, identity, temporal, and policy
engines. Unresolved production cases cannot become fabricated statuses or steps.

## Environment and executed checks

- Windows, CPython 3.14.3, existing pytest 9.1.1.
- Runtime: standard library; no package installation or provider calls.
- Final test command: `python -B -m pytest -q -p no:cacheprovider code/tests`.
- **89 passed in 2.28 seconds** in the final observed invocation.
- The first sandboxed invocation had 60 passes and 26 temporary-directory setup
  errors. The unchanged suite passed all 86 tests outside that sandbox. Three
  subsequent guard/integration cases brought the final suite to 89 passing tests.
  The setup errors were environmental and were not counted as passing tests.

## Measured results

| Measurement | Result | Interpretation |
|---|---:|---|
| Real request input validation | 518 loaded | Input coverage, not prediction correctness |
| Real processing diagnostics | 518 unresolved | No fallback labels; normal runner exits 3 |
| Public reference contract check | 32 rows, 193 steps accepted | Structure, plan relations, citation IDs and metadata cutoff checks only |
| Synthetic status agreement | 3/3 | Handwritten independent synthetic expectations |
| Synthetic exact-row agreement | 3/3 | Includes ordered steps, states, and citations |
| Synthetic step precision/recall/F1 | 1.0 / 1.0 / 1.0 | 21 synthetic steps; not challenge performance |
| Synthetic field agreement | 147/147 | Seven fields per synthetic step |
| Synthetic exact sequence agreement | 3/3 | Empty non-deletion sequence included |
| Synthetic operation coverage | 15/15 | Producer and checker independently compared with official table |
| Public sample production accuracy | NOT MEASURED | No predictions for those cases |
| Full-dataset/hidden accuracy | NOT MEASURED | No implemented audit engines or hidden labels |
| Semantic citation/policy/identity validation | NOT IMPLEMENTED | A contract-valid report explicitly says semantic support NOT_CHECKED |

The public labels have 10 COMPLETE and 22 INCOMPLETE cases, with no NOT_APPLICABLE
case. They are already inspected development references, not an untouched holdout.

## Additional independently specified cases

The three synthetic cases live in `ghosttrace/demo.py`; their public expected
representations are hand-specified separately in
`tests/fixtures/contract_cases.py`, without importing the producer registry,
canonicalizer, or mapper.

1. **Synthetic complete:** supplied compliant premises produce six verification
   operations with eligible synthetic citations. No findings/remediation.
2. **Synthetic incomplete:** supplied residual, exposure, active-flow, and restore
   premises produce five findings, five remediation operations, and five future
   verifications. Future evidence IDs are empty. Inputs are deliberately shuffled.
3. **Synthetic non-deletion:** supplied non-deletion authorization produces
   NOT_APPLICABLE and an empty array. It needs no deletion-coverage assertion.

These are contract-level cases, not realistic end-to-end audit benchmarks. Later
phases must add independently authored identity, timestamp, retention, replica,
and recreation scenarios. The current cases never provide production answers.

## Evaluator semantics and negative controls

- Status and exact-row accuracy use the reference-case denominator. Missing and
  extra cases are also listed explicitly; extra rows fail contract validation.
- Step precision/recall use multiset overlap of phase, system, resource,
  operation, state, and evidence ID, excluding step numbering.
- Field alignment uses phase/system/resource/operation, preserving occurrence
  order for duplicate alignment keys. Missing/extra steps count as seven wrong
  fields. Numbering remains a compared field.
- Sequence comparison retains the full ordered list and every field. JSON
  whitespace and object-key ordering are ignored by parsing.
- Undefined denominators produce null rather than a fabricated perfect score.
- Mutations test wrong status/state/phase, missing/extra fields, Boolean step
  numbers, missing/unknown/late citations, future-action citations, duplicate
  operations, missing plan relationships, reordered rows/steps, malformed CSV,
  duplicate JSON keys, non-finite JSON, and NUL content.
- A deliberately broken producer order is rejected by the independent checker.
- The comparator CLI accepts the independent synthetic expectations, then
  detects an intentionally corrupted candidate status.
- Writer tests simulate a replacement failure and preserve the previous artifact.
- CLI tests run from another working directory and forbid demo publication into
  the dataset or final root output.

## Smoke timings and determinism

Single local subprocess observations, including Python startup; these are not
statistical benchmarks or optimization claims:

| Invocation | Observed seconds |
|---|---:|
| Validate 518 request rows | 0.3182 |
| Diagnose 518 unresolved cases | 0.3479 |
| Compile synthetic demonstration | 0.3526 |
| Validate public reference contract | 0.3283 |
| Inspect public sample contract | 0.3603 |

Two observed demonstration runs produced identical SHA-256:
`6a4c619dcf69df3be39fb0e03abefd02dc6cbb2559181051eb94c90f0ea3bd58`.
The writer test also reverses supplied decision order and verifies identical bytes.
This establishes repeatability for fixed synthetic premises only.

## Before, after, and remaining risks

Before: two empty entry points; no executable contracts, validator, or tests.
After: a runnable contract boundary and independent checks with 89 passing tests.
No before/after challenge accuracy or speedup can be computed from an absent
baseline.

Remaining: evidence-content parsing; historically qualified identity; time/state
reconstruction; policy interpretation; semantic citation support; retained-record
safety; dependency-aware planning; selective model extraction; complete production
predictions. Metadata eligibility does not prove any of these.

## Skills and validation evidence

- `orchestrate-build`: applied typed boundaries and explicit failure handling;
  verified through loader, CLI, writer, and malformed-output tests.
- `hackerrank-orchestrate-design`: applied exclusive emitter ownership and
  uncertainty separation; verified through unresolved-decision and architecture
  boundary tests.
- `hackerrank-orchestrate-evidence`: separated synthetic, contract, and unmeasured
  semantic claims; actual test output and CLI observations are preserved in the
  genuine Codex session trace and summarized here.

No causal skill-effectiveness experiment was run. Phase 02 has not started.
