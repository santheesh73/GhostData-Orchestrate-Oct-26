> HISTORICAL BASELINE AUDIT (9f534ca/fc69092): current recovery status is in RECOVERY-REPORT.md and code/evaluation/evaluation_report.md. The original findings below are preserved.

# GHOSTTRACE phase-wise engineering audit

Audit date: 25 October 2026. Branch: main. Current baseline:4278de1;
application source reviewed at the Antigravity merge fc69092. The later commit
adds handoff documentation only. This report uses the independently reproduced
handoff measurements; no source edits, new predictions or repeated test runs were
needed for this reporting turn. It follows the user's original Phase00–07 plan,
not the different numbering used by generic skills.

## Overall decision

The implementation runs end to end and produces a structurally valid518-row CSV.
It is **not fully verified for submission**. Internally resolving every request
is different from proving every decision. Counterexamples demonstrate unsupported
policy assumptions and fabricated document observations that can pass current
gates. Phases00–02 are complete within their stated scopes; Phases03–06 require
correctness follow-up; Phase07 artifacts exist but final acceptance is blocked.

| Phase | Scope | Audit status |
|---|---|---|
| 00 | Repository/specification audit and architecture | Complete; documentation needs current-state reconciliation |
| 01 | Contract engine and runnable baseline | Complete within the agreed contract/synthetic-baseline scope |
| 02 | Structured evidence ingestion | Complete for supported structured formats; semantic interpretation is later scope |
| 03 | Historical identity and temporal reconstruction | Implemented; correctness follow-up required |
| 04 | Policy and risk decisions | Implemented; confirmed correctness failures |
| 05 | Selective document/AI extraction | Local capture works; semantic extraction fails grounding controls |
| 06 | Evaluation and optimization | Measurement tools work; corrective exit gate not passed |
| 07 | Freeze and submission | Bundle built; final readiness blocked |

## Phase00 — repository audit and architecture lock

**Verified:** designated GhostData origin, merged main, official AGENTS.md and
problem_statement.md, participant-data boundaries,518 evaluation requests,
32 public samples,94 evidence files, exact output contract,15 allowed operation
triples and the existing modular architecture. Official inputs were unchanged by
Antigravity's merge. No replacement architecture is required.

**Follow-up:** README/EVIDENCE-GAPS still describe375 resolved/143 unresolved,
while report headings declare all gates passed. Treat these as stale/conflicting
claims. The challenge deadline remains unconfigured; no remaining-time claim is
made. Earlier Codex changes were preserved in a named local stash, not discarded
or merged blindly.

**Exit:** accepted as the historical audit/planning phase. Update living status
records as repairs produce new evidence.

## Phase01 — contract engine and runnable baseline

**Implemented:** typed models, operation registry, loaders, pipeline boundaries,
canonical ordering/emission, independent CSV validator, atomic publication and
CLI entry point. Sources: code/ghosttrace/models.py, spec_registry.py, pipeline.py,
emit/, quality/validator.py and code/main.py.

**Verified:** fresh isolated full publication exits0, writes518 sorted rows and
matches the submitted CSV semantically. All three statuses and the output schema
validate. Raw-byte formatting differs without changed parsed rows. No root
output.csv is tracked; submission/output.csv is tracked, and a clean checkout
must run the command to recreate the root output.

**Limit:** this completes execution/contract scope, not semantic correctness.
The validator explicitly reports semantic_support=NOT_CHECKED. Phase01 was
previously narrowed, with user approval, to contract/synthetic-baseline behavior;
that historical acceptance is preserved rather than redefined retrospectively.

## Phase02 — structured evidence ingestion

**Implemented:** CSV/JSON/SQL/log readers, normalization, provenance hashes,
evidence index, diagnostics, and manifest-based source access. Sources:
code/ghosttrace/ingest/ and code/tests/test_ingest.py, test_structured_parser.py,
test_corpus.py, test_evidence_index.py.

**Verified:** the augmented run accounts for all94 manifest files, with no
ingestion errors. All15 PDF/PNG sources are captured locally in Phase05.
Antigravity removed the catalog label==user-ID restriction, a genuine parsing
repair that must be retained.

**Limit:** PARSED means capture/parsing succeeded; it does not prove all facts
were understood correctly. Catalog identity linkage is not a deletion-state
readback. Structured ingestion is accepted within that scope; downstream
interpretation remains open.

## Phase03 — historical identity and temporal reconstruction

**Implemented:** current/historical aliases, ownership intervals, reassignment
handling, resource linkage, replay, physical-copy state and conflict resolution.
Sources: code/ghosttrace/resolve/.

**Verified:** historical/temporal regression tests pass within the413-test suite;
cutoff filtering remains implemented, and catalog link parsing improved.

**Open issues:** resource/type fallbacks use names/prefixes where explicit schemas
are absent. Replay now gives archive presence to restore authorization decisions,
which requires a direct archive-state justification; authorization alone need
not prove storage state. Document-created identities/IDs can contaminate later
reconstruction even when timestamp filtering is correct.

**Exit requirement:** require explicit eligible subject/resource bindings and
state observations; preserve UNKNOWN where only a claim or fabricated document
projection exists. Add counterfactual authorization-versus-readback checks.

## Phase04 — policy and risk engine

**Implemented:** deletion authorization, obligations, retained records,
tombstones, PII checks, flows, restore risks and ordered remediation/verification.
Sources: code/ghosttrace/policy/.

**Confirmed defects:**
- obligations.py:49 treats presence/scan results as sole-subject ownership.
  A synthetic attachment with only a subject email gets a DELETE_RECORD plan,
  although exclusive ownership was never supplied.
- obligations.py:69 accepts a missing retention expiry as satisfying the supplied
  retention condition;:90 treats record presence as an active legal hold.
  Minimal synthetic records receive COMPLETE without those condition facts.
- obligations.py:252 turns unknown restore permission into allowed=True.
- The shared-context fallback accepts generic presence rather than establishing
  the conversation condition. Tombstones accept inactive as well as deleted,
  despite the report describing strict deleted-only behavior.
- Nonempty message_excerpt is no longer part of the final uninterpreted-text
  guard; arbitrary residual content requires stronger negative-PII checks.

**Exit requirement:** three-valued conditions must stay unknown unless supported;
preservation precautions must not masquerade as established compliance. Add
negative/ambiguous ownership, hold, retention, excerpt and restore fixtures.
**Phase04 is not complete.**

## Phase05 — selective document/AI extraction

**Implemented:** PDF text, native Windows OCR, content hashes, cache, model-output
validation, optional provider, bounded attempts and usage accounting. The Win32
stream bridge fixes native OCR access in this environment. Sources:
code/ghosttrace/extract/.

**Verified:**15 local PDF/PNG sources captured,25 business-schema projections
reported, no provider calls. Existing optional-provider tests use synthetic
transports. No live model/provider validation occurred, and other-platform OCR
was not independently verified in the handoff.

**Confirmed defects:** business.py:75/:78/:81 synthesize export/tombstone/object
IDs from statement/user/filename numeric suffixes. A panel containing only
Production workspace and user_913 creates tombstone_913 plus deleted status and
null PII fields. An object-storage heading plus filename creates object_842 and
sole_subject=true. business.py:105 infers connector/scheduler booleans from generic
words anywhere in a panel; missing keywords become false. These are unsupported
observations, despite attached citations.

**Exit requirement:** bind each literal ID, identity and state to its own row or
panel. Never invent cleared fields, exclusive ownership, scheduler state or ID
translations. Measure interpretation quality separately from text capture. Live
model validation is conditional on choosing that optional path; no paid call is
a prerequisite if a correct native solution covers the evidence.
**Phase05 is not complete.**

## Phase06 — evaluation and optimization

**Implemented:** blind-runtime-then-public-label comparison, case/step/field/
sequence metrics, traces, failure taxonomy, regression/metamorphic controls and
cached/reference benchmarking. Sources: code/evaluation/, code/tests/.

**Independently reproduced:**

| Metric | Result |
|---|---:|
| Existing suite |413 passed in21.42s|
| Full-input internal decisions |518/518;0 unresolved|
| Computed COMPLETE / INCOMPLETE / NOT_APPLICABLE |155 /353 /10|
| Public authorization agreement |32/32|
| Public publishable status agreement |25/32 (78.125%)|
| Public abstentions |7|
| Exact rows / sequences |5/32 (15.625%)|
| Step precision |137/142 (96.48%)|
| Step recall |137/193 (70.98%)|
| Step F1 |81.79%|
| Field agreement |914/1386 (65.95%)|
| Provider calls / input tokens / output tokens |0 /0 /0|
| Model-service cost |USD0; excludes development/local compute|
| Hidden/full-dataset accuracy |NOT MEASURED|
| Semantic extraction recall |NOT MEASURED|

The public command exits1 because outputs are imperfect. Missing sample rows:
case_01, case_02, case_04, case_10, case_12, case_13, case_15. These are abstentions,
not seven observed wrong emitted statuses. Only five complete sequences match;
25 correct statuses must not be described as25 correct full answers.
137/142 precision means five predicted steps do not match; the report's zero
false-positive-steps claim is inconsistent. Public labels were previously
inspected and are not a held-out trial. The413 existing tests omit the confirmed
handoff counterexamples. No fresh performance speedup or cross-platform
reproducibility claim is established by this audit.

**Exit requirement:** repair generalized failures, add adversarial controls,
rerun all public diffs and full publication, and verify determinism on corrected
semantics. No arbitrary100% hidden-accuracy target is assumed, but known contract
violations cannot be closed by passing structural tests.
**Phase06 is not complete.**

## Phase07 — freeze and submission

**Present:** submission/output.csv, code.zip, README, evaluation/usage reports
and log copy. The code archive has90 members, required entry/report files, no
duplicate entries and none of the checked prohibited dataset/cache directories.
Its normalized Python content matches the inspected source; the reported byte
mismatch is line endings only. Fresh isolated publication reproduces the parsed
submitted output. This is not a comprehensive secret or trace-completeness audit.

**Blockers:** semantic defects above, contradictory/stale documents, and a weak
scripts/package.py gate. The packager checks row count/order/status/JSON arrays,
but does not independently enforce exact request-ID coverage and every operation
field or semantic support; asserts can also be disabled. Authentic logs exist,
but final transcript/trace completeness, interview readiness and an authenticated
upload were not verified. No submission upload occurred in this review.

**Exit requirement:** freeze corrected source, produce one final verified output
and corresponding usage report, reconcile README/design/decision records,
validate explicit archive contents and transcript/trace selection, and rebuild
from that exact state. **Artifacts exist; Phase07 is not accepted as final.**

## Repair order

1. Remove unsupported document IDs, redaction defaults and process booleans.
2. Restore evidence-backed policy conditions, ownership and restore-state checks.
3. Add the demonstrated adversarial fixtures and preserve genuine OCR/catalog fixes.
4. Re-evaluate all cases, inspect whole-plan diffs and separate actual data gaps.
5. Reconcile reports; strengthen packaging; freeze only after those gates pass.

No application logic or dataset was changed for this report. Earlier Codex
working changes remain preserved in stash569016ae1ab137511cab88551be761b4f1621384.
Detailed counterexamples and source locations are in HANDOFF-REVIEW.md; private
reproduction outputs remain under ignored .ghosttrace/handoff-*.
