# GHOSTTRACE Phase 05 evaluation report

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
