# GHOSTTRACE usage status through Phase 03

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
