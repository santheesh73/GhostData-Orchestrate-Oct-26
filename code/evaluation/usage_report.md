# GHOSTTRACE Phase 01 usage status

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
