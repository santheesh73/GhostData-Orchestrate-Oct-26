# GHOSTTRACE Phase 01 evaluation report

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
