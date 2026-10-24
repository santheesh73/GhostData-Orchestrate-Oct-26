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
