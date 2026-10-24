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
