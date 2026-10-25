# Phase 06 repair usage — current status

Two real guarded full-input runs, both public-evaluation configurations and the
cached/reference comparisons used **0 provider calls, 0 input/output tokens and
USD0 model-service cost**. Per-request native tokens/cost are zero; per-model totals
are empty because no model/provider was selected. Cached model-build usage is
also zero. This excludes Codex development usage/local compute. No packages were
installed and no paid model call occurred.

Both fresh full runs process 518 requests and exit 3: 375 audits resolve and 143
remain unresolved. No root output.csv was published. These are diagnostic/blocked
publication usage figures, not a successful final prediction run. The required
final-run report remains unavailable; its presence on disk is not readiness.

---

# Archived initial Phase 06 usage

Phase 06 public evaluation (32 requests in each of structured and extraction-
augmented modes), the 518-request alternating reference/cache benchmark and two
fresh 518-request augmented diagnostics all used **0 provider calls, 0 input
and output tokens, and USD 0 model-service cost**. No provider/model was selected
for these runs. Diagnostic tokens and model cost per request are also zero;
per-model totals are empty. Cache-build model usage was zero. These measurements
exclude local compute and Codex development-session usage.

The offline evaluator hard-disables provider calls rather than inheriting any
optional model environment configuration. The benchmark times native engines and
makes no label requests. No dependencies were installed. Full-run statuses remain
10 NOT_APPLICABLE and 508 unresolved. No root output.csv was created, so these are
not final prediction-run usage figures. The required final-run report below
remains unavailable. Phase 07 freeze/submission has not started.

---

# Archived usage status through Phase 05

## Phase 05 measured runs

Local capture of all 15 PDF/PNG sources and two augmented 518-request diagnostic
runs used **0 provider calls, 0 input tokens, 0 output tokens and USD 0 model
service cost**. No provider was configured, and call budgets defaulted to zero.
This excludes local compute cost and Codex development-session usage, which are
not measured by this application. No production output.csv was generated.

The optional adapter records actual returned model names, reported input/output
and cached-input tokens, refusals/failed attempts and unknown usage. Missing token
counts or pricing produce unknown totals/cost; user-provided USD-per-million
rates supply estimates without hardcoded prices. Cached build attempts, including
retries, are separate from zero-call replay. No live provider behavior or pricing
was validated in this phase; provider tests use explicitly synthetic transports.

Cache/usage files under .ghosttrace/ are private runtime artifacts and excluded
from Git. Required final prediction-run fields below remain unavailable.

## Phase 04 runtime

Authorization grammar, supplied-policy evaluation, risk checks and plan assembly
use only the standard library and existing evidence index. Full 518-request
policy diagnostics make zero provider calls and consume zero provider input or
output tokens; model service cost is zero. No packages were installed. This does
not measure Codex development-session tokens, local compute cost or a final
prediction-producing run.

The real corpus still has unresolved cases and no root output.csv. The three-case
synthetic policy roundtrip in tests is not a production usage report. Final-run
fields below remain unavailable. Phase 05 has not started.

## Phase 03 runtime

Historical ownership, resource linking and temporal replay use only the standard
library and the Phase 02 in-memory evidence index. Two final full reconstruction
diagnostic runs each processed 518 requests. For those executions, provider
calls/input tokens/output tokens were 0/0/0; model service cost was zero. No
packages were installed. This is not a final prediction-run usage report and
does not measure Codex development-session tokens or local compute cost.

No production decisions or root output.csv were generated. The required final
run fields below remain unavailable until the output-producing run occurs.

## Phase 02 runtime

Structured parsing/indexing and its CLI coverage runs use the standard library,
including restricted in-memory SQLite. No provider adapter, external extraction,
or network call is used by this runtime. Provider calls/input tokens/output tokens
for these executions are 0/0/0. These values are not a final prediction-run cost
report and do not include Codex development-session usage, which was not measured.

All 518 real decisions remain unresolved; no final root output.csv exists.
The final-run reporting fields below therefore remain unavailable.

## Required final-run report

**NOT AVAILABLE YET.** No final full-dataset prediction run has occurred and no
root `output.csv` has been produced. This file must be updated from that actual
run before submission; its current presence is not submission readiness.

| Final-run field | Current value |
|---|---|
| Providers and model names | NOT APPLICABLE YET |
| Model calls, input tokens, output tokens | NOT MEASURED FOR A FINAL RUN |
| Total / average tokens per request | NOT MEASURED |
| Total / per-request estimated model cost | NOT MEASURED |
| Per-model and overall totals | NOT APPLICABLE YET |

## Observed Phase 01 runtime checks

The input diagnostics, contract checks, and three-case synthetic compiler make
no model/provider calls. Runtime has no provider adapter or network dependency.
For those Phase 01 executions: provider calls = 0, provider input tokens = 0,
provider output tokens = 0. These values do not represent final-run usage or the
Codex development session's token consumption. Development-session usage was not
measured by this project.

Later extraction must record exact providers/models, retries, actual usage,
cache behavior, and pricing provenance. A cached replay must identify the cost
of building its extraction cache separately rather than disguising it as a
zero-cost full audit. No secrets or credentials belong in this report.
