# GHOSTTRACE engineering decisions

## Phase 01 — approved scope

The Phase 00 architecture remains frozen: specification registry, ingestion,
historical identity/temporal reconstruction, policy/risk judgment, canonical
emission, and an independent quality gate. Phase 01 implements the contract
boundary and a synthetic end-to-end demonstration, not deletion auditing.

The user approved the Phase 00 blueprint by saying “Start the Phase 1”. Its gate
correction is essential: loading all 518 requests does not establish their
answers. The normal runner records unresolved cases internally and refuses to
write predictions. No default COMPLETE/INCOMPLETE/NOT_APPLICABLE values stand in
for missing reasoning. Full prediction publication requires later phases.

## Contract and authority

- `AGENTS.md` sections 6.2–6.6 and `problem_statement.md` define public output.
- `README.md` places required reports inside `code/evaluation/`.
- The 15 operation/phase/state triples and their order are specification values.
- IDs remain opaque strings. Output sorting uses ascending string order; no
  numeric suffix interpretation or case-family assumptions are introduced.
- Only the emitter creates submission representation. Internal uncertainty,
  coverage, policy rationale, and source locations never become extra CSV/step
  fields.
- The validator has its own operation table and ordering checks. Tests compare
  both tables independently with the official statement, reducing shared-oracle
  errors. It does not call emitter logic to repair candidate outputs.

## Models and proof boundary

Standard-library frozen dataclasses establish interfaces without a mandatory
runtime package. Evidence availability timestamps are checked where metadata is
supplied. Existence and time eligibility do not establish citation meaning,
subject identity, policy applicability, or evidence completeness. These remain
unimplemented semantic checks. Demonstration decisions explicitly assert their
synthetic premises; they are never loaded from official sample answers.

## Failure and publication

Malformed input fails with actionable, non-PII diagnostics. Unresolved decisions
are distinct from official statuses. The writer validates before staging, checks
the staged bytes, and atomically replaces only a valid output. Demonstration
output is restricted to `.ghosttrace/`, preserving both dataset and submission.

## Evaluation

Public labels are accessed only by development evaluation. Comparison ignores
JSON object-key order/whitespace and preserves array order. Step precision/recall
exclude numbering so sequence errors can be diagnosed separately; field accuracy
includes numbering after alignment by phase/system/resource/operation. Missing
and extra aligned steps count as incorrect fields. No hidden accuracy is claimed.

## Skill use

`orchestrate-build` supplies typed boundaries, recovery, and verification;
`hackerrank-orchestrate-design` supplies output ownership and unknown handling;
`hackerrank-orchestrate-evidence` supplies source-bound claims and limitations.
Generic escalation fallbacks and historical score weights are not adopted.
Tests and measured results are recorded in `code/evaluation/evaluation_report.md`.

## Deferred

No evidence parsing, identity resolution, temporal replay, policy decisions,
model extraction, production output, or submission packaging is implemented in
Phase 01. No new services, agent framework, or dependencies are installed.

## Phase 01 exit and risk register

The corrected contract-baseline gate is satisfied by 89 passing tests, the
independently specified three-case synthetic roundtrip, and diagnostics for all
518 requests. See the evaluation report for commands, timings, and limits.

| Open risk | Current safeguard | Required next evidence |
|---|---|---|
| False completeness from unparsed evidence | All real decisions stay unresolved | Phase 02 format and coverage accounting |
| Wrong subject or historical state | No identity/time verdict is invented | Phase 03 ownership/cutoff fixtures |
| Retention or recreation mistake | No policy decision is made in this phase | Phase 04 policy/risk tests |
| Existing ID mistaken for semantic support | Validator explicitly marks semantics NOT_CHECKED | Source-content and derivation checks |
| Sample overfitting / missing non-deletion coverage | Runtime excludes labels; synthetic non-deletion fixture | Independent realistic authorization cases |
| Preliminary usage report mistaken for final | Final-run fields explicitly unavailable | Actual output-producing run and usage records |

Phase 02 requires explicit user approval; none of its engines are implemented.

## Phase 02 — structured ingestion (approved)

The user approved Phase 02 by saying “Start the Phase 2”. The new ingestion
modules remain inside Stage 1 of the frozen compiler architecture. No historical
identity merge, temporal state selection, policy judgment, or prediction was added.

### Provenance and lossless normalization

- Each file is read from the participant evidence namespace and SHA-256 hashed.
- Observation IDs bind file bytes, manifest metadata, relative locator, physical
  copy, and canonical payload. They contain no machine-specific absolute paths.
- Raw JSON values distinguish null, false, empty string, list, and object. CSV
  cells retain their string representation rather than guessing nulls/booleans.
- Original log lines, headers, nested envelopes, trace IDs, SQL schemas, snapshot
  scope rows, and SQL comments remain available in normalized payloads.
- Source availability and observation timestamps stay separate. Creation/expiry/
  update facts are not silently substituted for a snapshot's observation clock.
- A context identity row has no asserted file-availability timestamp and is not
  a permitted citation. Audit/activity rows keep their actual citeable IDs.

### Parsing and retrieval boundaries

JSON adapters follow nested snapshots, collections, and service exports, including
returned documents. SQL preserves each primary/replica table separately. Logs
support KV, bracket, pipe, syslog, JSON, and escaped cloud envelopes. Header/payload
conflicts are retained and diagnosed. Unknown or malformed units never silently
become successful observations. The handover text adapter retains unsupported
narrative as unparsed. Generic evidence CSV support is separate from context CSVs.

The exact-match index may expand candidates through a trace within the same file,
service, and instance. It does not propagate identity facts into other events or
merge people. Time-filtered searches report excluded future/unknown observations.
Every lookup explicitly has supports_absence=false. Scope metadata also says
completeness=NOT_ESTABLISHED; row counts do not prove global deletion.

### SQL execution boundary

Each dump uses a fresh `:memory:` SQLite connection, explicitly closed afterward.
Only table/index DDL, INSERT, transaction framing, and foreign_keys=ON are accepted.
An authorizer rejects attachment, file pragmas, extensions, virtual tables,
triggers, and functions other than the supplied json_valid constraint. Automatic
and declared indexes are allowed because the supplied snapshots require both.
Statement/row/VM budgets bound work. No on-disk database is created.

The standard-library API basis is the
[Python sqlite3 documentation](https://docs.python.org/3.14/library/sqlite3.html#sqlite3.Connection.set_authorizer).

### Constants provenance

| Limit | Value | Provenance |
|---|---:|---|
| Maximum evidence/context file | 16 MiB | JUDGEMENT safety bound, not sample tuning |
| JSON depth | 64 | JUDGEMENT safety bound |
| Record/statement budget | 100,000 | JUDGEMENT safety bound |
| SQLite progress interval / callbacks | 1,000 / 1,000 | JUDGEMENT, approximately one million VM operations per file |
| Log key / text email candidate bounds | 128 / bounded 256-local, 255-domain, 63-suffix components | JUDGEMENT to bound scans; explicit typed fields remain preserved |

### Phase 02 exit and remaining risks

149 tests passed, including all Phase 01 regressions. All 94 manifest files are
accounted for: 79 structured sources parsed without diagnostics and 15 PDF/PNG
sources deferred. Four context CSVs parsed. Two runs produced the same indexed
observation fingerprint; see the evaluation report for measurements.

Remaining risks: parsing is not semantic extraction recall; real evidence can
contradict itself; identity snapshot availability is incomplete; partial/failed
sources must block future completeness claims; document extraction is pending;
trace candidates do not establish ownership. Phase 03 must consume these facts
without treating source order, absence of hits, or operation SUCCESS as verdicts.

Actual skill guidance applied: `orchestrate-build` for strict boundaries/failure
isolation, and `hackerrank-orchestrate-evidence` for source hashes, genuine test
evidence, and explicit unknowns. No skill-effectiveness experiment was run.
No packages, model providers, new services, or submission artifacts were added.
Phase 03 has not started.

## Phase 03 — temporal identity engine (approved and completed)

The user approved this phase with “Start Phase 3”. The historical statements above
record earlier phase boundaries; this section describes the current state.
Stage 2 now consumes Stage 1 observations without changing the frozen compiler,
the official inputs, the output schema, or the exclusive emitter boundary.

### Ownership and account/resource links

`resolve/identity_graph.py` builds an ownership graph rather than a union-find
merge of identifiers. Audit old/new transitions define half-open intervals, with
both boundary events retained in the proof. Equal-time contradictory changes and
broken old/new chains remain uncertain. Exact current/historical aliases stay
separate by email, phone, and hash namespace; names do not resolve a subject.

Request matching prefers an owner supported at requested_at. A uniquely owned
historical email remains usable after retirement, while competing historical
owners remain ambiguous. Audit events and their availability must be at or before
audit_at. A future registry entry cannot reinterpret an earlier untyped reference.

An identity snapshot has no capture clock in the supplied contract. Its update
time is not used as availability. Snapshot matches therefore remain CONTEXT_ONLY
unless audit history or an eligible stable-reference/identifier pair corroborates
them. A pair must be present in one object, not assembled across unrelated nested
messages. Such a pair establishes a point observation, not lifelong ownership.

`resource_links.py` links exact identifiers/stable references to scoped resources.
Multiple accounts may link to one stable subject, without merging resources or
people. Historical links can retrieve later redacted/absent readbacks. A later
alias assignment cannot propagate backwards; after reuse, a stale alias alone
cannot disambiguate ownership. Resource ownership conflicts remain AMBIGUOUS.
Dedicated catalog-link messages remain PROVISIONAL until corroborated. Their
schema adapter accepts opaque IDs and does not trust reported_result.

Trace lookup continuation requires the same evidence file, system and physical
instance, and a preceding/equal-time identity-bearing event. All contributing
trace and ownership observation IDs survive in the link proof. Resource IDs in
different systems stay separate; logical aliases or copy equivalence are not
invented from similar names.

### Replay and conflicts

`temporal_replay.py` extracts scoped presence readbacks, named process flags,
identifier fields, and source-supported scan matches. Named event adapters are
schema interpretations, not sample-label or case-family rules. Unknown event
names remain timeline claims with no direct state extraction. Operation SUCCESS,
cache misses, started queries, and missing inventory rows cannot prove deletion.

`conflict_resolver.py` selects the newest eligible observation for each dimension
within system/resource/copy. Equal-time incompatible values retain every proof
and return unknown. There is no SQL/JSON/log priority or evidence-ID tie breaker.
Explicit JSON null is distinct from unknown; a later omission/absence invalidates
an older identifier as current-state evidence. Categories with competing raw
names remain unknown pending policy normalization.

Facts carry their observation times; latest observed is not a guarantee of
continuous coverage up to audit_at. A source-specific instance/table scope is
not automatically a distinct physical storage copy or a globally complete search.
No absence is inferred outside an explicitly scoped readback.

### Integration, validation and remaining work

`--reconstruct-evidence` ingests once and reconstructs all selected requests. Its
PII-free summary contains counts, uncertainty codes and source-bound hashes.
The default runner still returns exit 3 with all 518 decisions unresolved because
policy is not implemented. It never writes a provisional official status.

209 tests passed. Two full runs in separate processes/hash seeds returned the
same diagnostics and proof hash. The evaluation report records actual coverage,
timings, synthetic cases and review corrections; no accuracy claim is inferred
from these counts. No packages, providers, services or model calls were added.

Skills applied: orchestrate-build (typed proof boundaries),
hackerrank-orchestrate-design (explicit unknowns and output ownership), and
orchestrate-test-fix with dataset-coupling/determinism references (opaque-ID,
ordering, temporal counterfactual and cross-process controls). Historical score
claims, generic escalation output labels, goal mode and later-phase directions
are not adopted. No skill-effectiveness experiment was run.

Remaining: 417 provisional request identities; some provisional resource links
and claim-only state scopes; 15 deferred documents/images; unmeasured semantic
recall/identity/state accuracy; policy/category normalization and decisions;
semantic citation enforcement; remediation ordering; production output and final
submission. Phase 04 is not started.

## Phase 04 — policy and risk engine (approved)

The user approved Phase 04 with “Start the Phase 4”. Earlier phase statements
above are historical. The new policy layer consumes reconstruction and feeds the
existing emitter, without changing the frozen stages or official contract.

### Applicability and rules

Request authorization uses conservative grammar, negation/conflict checks and
explicit unknowns. It reads request_text, never reported_status or evidence
instructions. Supported affirmative grammar includes English, Portuguese, Spanish
and French forms; unsupported scripts, quoted/hypothetical instructions and
unclear mentions defer. This is not a general multilingual language model.

The initial full run exposed a concrete mistake: “would like it permanently
deleted” lacked a request cue, and “correct treatment” in a later sentence could
then be misclassified as a correction request. Adding the missing grammatical
cue and keeping unscoped deletion mentions unresolved fixed this. Regression
fixtures cover that counterexample, retention exceptions, conflicting requests,
other actions, negation, reported speech and unsupported languages. No public
answer labels were consulted or runtime case-family rules introduced.

Rules are loaded literally from the supplied CSV with unique IDs/categories and
known action types. Named adapters implement its conditions as true/false/unknown;
unknown/new condition text is never executed or treated as Always. Collection and
event mappings interpret participant schemas, not resource-ID prefixes. A
condition that is false does not invent an alternative deletion policy. Explicit
cleared attribution/email fields can establish an already satisfied treatment.

### Preservation, exposure and recreation risks

- Retention dates are compared at audit_at, with exclusive retention_until.
  Missing/expired retention or inactive/unknown holds leave the alternative policy
  unresolved. Required retained records must remain present. Their absence cannot
  be repaired by inventing an operation outside the official vocabulary.
- Support conversations require shared-context evidence before redaction;
  attachment deletion requires subject-only evidence. Unsupported free text defers.
- Analytics anonymization removes subject references as well as direct identifiers.
  Tombstone redaction preserves the supported stable reference and clears name,
  email, phone, hash and additional direct identifier fields, including nested
  values. Unknown/omitted fields are distinct from explicit null or empty values.
- Exact subject identifiers in supported message fields establish exposure.
  Nonempty unsupported narrative cannot prove absence of PII. Agent/staff fields
  in shared support records are not treated as the customer's direct fields.
- Flow enabled/readback facts establish active/disabled state. Contradictory or
  malformed scheduler controls cannot silently become disabled-flow proof.
- Backups are retained; restore_allowed and supported eligibility/block fields
  establish restore risk. Complete blocked-restore verification also needs the
  archive's presence. No backup DELETE action is generated.
- SQLite 0/1 is adapted only for named Boolean fields in SQL records; JSON
  integers and malformed Boolean representations remain unknown, not truthy.

### Proof and planning boundaries

Every assessment retains rule, resource/copy, outcome, supporting observation
IDs and proposed operations. Complete conjunctive verification requires a single
eligible artifact supporting all required state fields. Findings cite positive
state evidence. For incomplete plans all remediation and future verification
citations are empty, including verification of already compliant retained scopes.

The planner combines copies while retaining internal per-copy assessments.
Incompatible actions for one public system/resource block publication. Explicit
typed source/downstream endpoints are checked against canonical operation order;
if the contract cannot express a safe dependency order, the case remains unknown.
Disable/block operations otherwise precede record changes by the official table.

The new audit gate checks authorization/status/assessment consistency, protected
categories, proof presence, source clocks/roles, exact derived operations and plan
coverage. It does not duplicate the producer's complete policy interpretation.
The existing independent CSV validator remains a separate structural check.
Handwritten fixtures test semantic rules; source checks alone are not proof of
semantic correctness or recall.

The normal lightweight diagnostic reports POLICY_AUDIT_NOT_RUN.
`--audit-policy` performs the real audit without writing a CSV. The checked audit
publication API is exercised only on synthetic premises in tests. An explicit
coverage_complete Boolean is an internal asserted premise, not inferred from
file parse success. Production integration does not set it: inventory scopes
still say NOT_ESTABLISHED and 15 files remain deferred. Partial findings survive
internally but cannot be emitted as a complete final plan.

### Validation and remaining work

285 tests pass, retaining all 209 earlier tests. Synthetic complete/incomplete/
non-deletion cases roundtrip through the audit gate, emitter, independent
validator and writer. Full 518-request diagnostics are reproducible across fresh
processes/hash seeds; actual metrics and limits are in the evaluation report.
Ten non-deletion decisions resolve; 508 cases remain unresolved, including 24
unsupported-language requests. Resource-scope assessments are not accuracy scores.

Applied orchestrate-build guidance for typed seams/failure isolation and
hackerrank-orchestrate-design for explicit unknowns and output ownership. No
skill-effectiveness experiment, provider call, package installation, new service
or framework was introduced. Official files/dataset are preserved. Phase 05
document/image/language extraction and subsequent coverage/evaluation/release
work remain pending. No root prediction CSV or submission archive was created.

## Phase 05 — selective extraction (approved)

The user approved “Start the Phase 5” and then “Continue the phase 5”. Stage 1
now accepts optional document extraction and the policy layer accepts a selective
intent resolver. Earlier phase statements above preserve their historical scope.
The compiler stages, output contract and publication gates remain unchanged.

### Local capture and source grounding

PyMuPDF extracts all text blocks/pages from native PDFs. Scanned pages can render
to a temporary bitmap for OCR. Pillow validates image bytes/dimensions; OCR uses
Windows OCR en-US through Windows PowerShell 5.1 or optional Tesseract English
on another platform. Document paths are passed as data, never interpolated into
program text. The fixed reviewed Windows helper changes no profile or execution
policy and closes its bitmap/stream. No source document is modified.

Capture retains source SHA-256, manifest origin/capture time, page/block/line
locators, text and bounding boxes. DOCUMENT_TEXT observations are retrieval
candidates. They cannot establish identity, absence or compliance by themselves.
Only an explicit resource anchor plus validated literal fields becomes a
RECORD_SNAPSHOT. Source/system/category mappings are declared schema adapters;
ambiguous business artifacts retain an empty category instead of a guessed rule.
Documents have separate source-specific view scopes rather than inferred replica
equivalence. Capture time is the observation time of the artifact, not a new
timestamp invented by a model or a backend-state guarantee.

The structured extraction schema excludes verdicts, actions and caller-selected
evidence IDs. Every field needs a known name, exact quote and locator; resource
anchors must be explicit. Boolean/null values need explicit source literals.
Missing fields, masked screenshots and empty OCR cannot prove deletion or
redaction. Quote grounding verifies transcription consistency, not the truth of
the underlying business claim or perfect OCR accuracy. Free narrative that cannot
meet the literal schema remains unknown.

Extraction proof metadata is reserved and skipped by identity/temporal/policy
walkers. Otherwise a proof's field-name label could itself become a fake personal
name or identifier; a dedicated regression prevents that.

### Selective model seam and recovery

Native authorization remains first. Only unresolved language/intent paths can
use the optional resolver; supported grammar does not require calls.
Recognized quotation/hypothetical/override patterns remain unresolved. The returned
authorization is an enum with an original quote and negation-preserving English
translation, checked for consistency by native code. This guard does not prove
translation accuracy.

The optional OpenAI Responses transport uses strict JSON schema, store=false,
fixed API endpoint, disabled redirects, sanitized errors and no SDK dependency.
Model and credentials come from environment; no model or rates are guessed.
The transport follows the official
[Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).
The local OCR integration uses Microsoft's
[OcrEngine API](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr.ocrengine?view=winrt-26100).

Calls require an explicit budget, default zero. Limits are at most 64 attempts
per run and 3 per task. Refusals/permanent failures do not retry; transient or
invalid structured responses are bounded. No source content becomes executable
code. No configured provider was available in the actual verification runs, so
live model behavior/account compatibility remains unverified. Test doubles verify
transport, extraction and policy integration without pretending to be live runs.

### Cache and usage provenance

Atomic private caches live in ignored .ghosttrace/. Keys bind source bytes,
manifest identity/path/origin/time, reader/runtime/helper identity, prompt/schema,
model configuration and image hash. Replay repeats schema/grounding validation.
Corrupt/stale entries are rejected. Cache digests detect corruption and source
mixups; they do not authenticate against a malicious user rewriting both a cache
entry and its digest. Caches can contain fictional participant identifiers and
must not enter code.zip or Git.

Usage separates current provider calls from historical cached build attempts,
including rejected/transient retries. Missing usage and rates remain unknown.
Actual returned model names and reported token counts are preserved. Costs are
estimates using user-supplied verified rates; omitted cache-token breakdown uses
the standard input rate. Development-session Codex usage is not measured here.

| Bound | Value | Provenance |
|---|---:|---|
| Source file | 16 MiB | Existing Phase 02 JUDGEMENT bound |
| Pages / image pixels | 32 / 20,000,000 | JUDGEMENT resource limits |
| Captured text / units | 2,000,000 chars / 20,000 | JUDGEMENT resource limits |
| Model input / output | 128,000 chars / 2,048 output tokens | JUDGEMENT call limits |
| Source cache / provider response | 8 MiB / 4 MiB | JUDGEMENT resource limits |
| Model attempts | 3 per task, 64 per run, default 0 | JUDGEMENT cost/recovery bounds |
| HTTP / OCR process | 30 sec / 45 sec | JUDGEMENT timeout limits |

### Verification and limits

340 tests passed, retaining the 285 earlier regressions. Controls cover actual
local OCR and blank images, swapped sources, all-page PDF capture, literal facts,
typed schemas, stale/corrupt caches, retries/refusals/budgets, source changes,
negation, model-to-evidence/policy integration, usage provenance and preserved
output. No dependencies were installed. Build/design/prompt guidance, PDF visual
review and official API documentation were applied; no skill-effectiveness
experiment was run.

Actual local capture reads all 15 formerly deferred files: 4 PDFs/7 pages and
11 PNGs, 992 text units, 1 anchored record, 10,729 total indexed observations.
These are capture/provenance counts, not evidence recall or semantic accuracy.
Fourteen documents still need interpretation; the one record also has only
partial semantic coverage. All 24 unsupported-language requests remain unresolved
without a provider. Fresh-process cached full audits match at 10 NOT_APPLICABLE
and 508 unresolved; no real deletion answer has been published.

Exhaustive coverage, time-qualified identities, unknown categories/conditions
and retained-state proof still require further evidence. Extracting every file
does not set coverage_complete. Live model verification, challenge accuracy and
final prediction-run usage remain unavailable. No root output.csv or submission
archive was generated. Stop before Phase 06.

## Phase 06 — observed failures and measured optimization

The user approved “Start the Phase 6”. Scope follows the kickoff's evaluation and
optimization phase, independent of similarly numbered community skill phases.
Phase 07 freeze/packaging remains separate. The typed compiler, participant-data
boundary, temporal rules, supplied policy and publication guards are preserved.

### Honest evaluation rather than inferred readiness

The development evaluator runs requests/audits/publication gates before opening
the already-inspected public labels. Runtime modules cannot import evaluation or
sample-label utilities. Missing rows count against all reference cases. Published
and candidate metrics remain distinct; diagnostics never call a CSV writer.
Status, exact-row, step, field and sequence comparison reuse the independent golden
diff. Reference metadata comes from the full allowed citation catalog, including
deferred files; capture success and semantic support are separate.

Both structured-only and extraction-augmented runs measure zero publishable rows
on 32 public samples: 0% status/exact-row/field/sequence accuracy. Candidate plans
overlap 9/193 steps (precision 1.0, recall 0.046632), but no candidate is publishable.
The additional document capture has zero measured semantic benefit in this
zero-model configuration. Hidden accuracy and semantic recall remain unmeasured.
Guard-based failure stages identify limitations without inventing model misreads.

Generalized authorization grammar improves agreement from 18/32 to 27/32.
Changes cover ongoing erasure, explicit permanent closure, scoped continuation,
benign quoted UI labels, account-related residual copies/contact details and
verification after self-reported account deletion. Minimal pairs preserve other
actions, negation, third-party/quoted commands and status-only questions. Five
sample authorizations stay unresolved. No complete sample sentence, case-specific
predicate, reported status or golden label was added to inference.

### Profile-driven cache, with an uncached reference

A pre-change profile identified IdentityGraph.at as the main processing hotspot.
The cache shares only immutable normalized snapshot candidates and alias/subject
indexes inside one fixed input graph. Context stays uncertain and undated; every
view filters temporal history and pairs by its audit cutoff. Precomputed pairs
are reused only when the eligible subject registry exactly matches. Future-only
registry entries force the original pairing path. No cached cutoff decisions or
cross-input state is reused. The uncached implementation remains selectable by
the development benchmark and temporal differential controls.

The final benchmark uses one common warm-up, alternating trial order and three
trials per configuration on 518 requests. Complete Audit fingerprints include
unpublished candidate plans, so matching unresolved statuses cannot hide a changed
plan. All seven fingerprints match. Median engine-plus-audit time changes from
12.872485 to 6.816385 seconds (1.8885× local speedup), with ranges
12.720762–14.212807 and 4.499196–7.250012 seconds. Startup, ingestion, label I/O and
fingerprinting are excluded. Peak memory is not measured. This improves processing
time without improving end-to-end answer accuracy.

Benchmark repetitions (3–10) are a JUDGEMENT measurement/resource bound, not a
classification threshold. The actual report uses 3 per configuration. All
reference/optimized mismatches abort the measurement. No framework or dependency
was installed, and no live provider was called.

### Validation, actual result and failed readiness gate

384 tests passed in 12.12 seconds, retaining all 340 earlier tests. New controls
cover 23 authorization cases, six temporal boundaries, immutable cache context,
three opaque-ID/timezone/order/future-noise policy cases, label access ordering,
traces, inference import isolation, cache paths, benchmark trial counts and a
deliberately broken candidate-plan fingerprint/benchmark. Review restored the
informational-question guard with two new counterexamples before committing.
Prior retained-record,
tombstone, restore, ordering and native PDF/OCR controls remain passing.

Two fresh extraction-augmented full runs with hash seeds 0 and 12345 return
identical entire reports: 10 NOT_APPLICABLE, 508 unresolved; 484 deletion
authorizations, 10 non-deletion, 24 unresolved; 134 violating, 42 compliant and
1,770 unknown scopes. The full diagnostic proof remains
c85b1c97969dca93f4c684aa77b1eccd19fd3d374dfae68f06cef408e802be22.
Each run uses zero provider calls/tokens and USD0 model-service cost; development
usage/local compute are excluded. No output-producing final run exists.

The evaluation/optimization implementation is present, but its accuracy/readiness
gate fails. Identity availability, semantic conditions/documents, unsupported
authorization and exhaustive resource/copy coverage need additional work before
freeze. No root output.csv, submission archive or submission-readiness claim is
created. Updated evaluation/usage reports distinguish these observed failures
from the passing implementation regressions. Phase 07 remains unstarted.
