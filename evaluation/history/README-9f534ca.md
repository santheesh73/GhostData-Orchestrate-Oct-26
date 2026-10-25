# GHOSTTRACE — Phase 06 repair

GHOSTTRACE audits deletion requests against the supplied identity registry,
historical changes, policy, activity stream and evidence. It resolves identity,
replays state at audit_at, plans policy-safe remediation and validates output.

**Phase 06 is still incomplete.** The current full run resolves **375/518**
audits (115 COMPLETE, 250 INCOMPLETE, 10 NOT_APPLICABLE), with **143 unresolved**.
These are computed outcomes, not measured hidden-label accuracy. No final
output.csv exists; the full-run command exits 3 and preserves any previous file.
See [EVIDENCE-GAPS.md](EVIDENCE-GAPS.md) for the remaining conditions and explicit
public-reference linkage gaps. No corrected dataset or official clarification
was available. Phase 07 freeze/packaging has not proceeded.

## Setup

Run from the repository root with Python 3.11+; this environment was verified with
CPython 3.14.3. Core parsing/policy/output code uses the standard library.

```text
python -m pip install -r code/requirements-dev.txt
python -m pip install -r code/requirements-extract.txt
```

These files list test and optional document dependencies. No packages were
installed during this repair. PyMuPDF/Pillow and Windows OCR en-US were already
available. Windows image extraction uses the reviewed Windows PowerShell 5.1
helper without changing execution policy. Other platforms need the optional
Tesseract executable/English data; that fallback has not been verified here.
Place the unchanged participant dataset at dataset/. Do not use organizer files.

## Audit and guarded full run

```text
python -B code/main.py --audit-policy --with-extraction
python -B code/main.py --run --with-extraction
```

The audit command prints diagnostics without writing predictions. The run command
attempts root output.csv only for all 518 requests from the official repository
paths. All audits, proof gates, complete case coverage and the independent CSV
validator must pass before atomic publication. It never inserts fallback labels
or writes a partial root file. Exit 3 means unresolved audits/publication blocked;
1 means ingestion errors; 2 means invalid input/invocation; 0 means the requested
operation succeeded. Current real --run exits 3. Required output columns are
case_id,deletion_status,steps_json; rows and typed steps follow the official order.

Document/usage caches stay under ignored .ghosttrace/extraction/. --cache-dir can
select another directory within .ghosttrace/. Captured text is not automatically
understood evidence. Positive business-panel and form adapters preserve source
hashes/locators; ambiguous OCR identifiers are never corrected by guessing.

## Evaluation and traces

```text
python -B code/evaluation/main.py --audit-samples --with-extraction
python -B code/evaluation/main.py --trace-case case_29 --with-extraction
python -B code/evaluation/main.py --benchmark-audits --with-extraction --repetitions 3
python -B -m pytest -q -p no:cacheprovider code/tests
```

These development commands never write predictions. The evaluator finishes
inference/gates before opening the public labels, which are already-inspected
development references rather than a held-out set. Sample comparison exits 1
when imperfect, 0 for exact agreement, 2 for input errors. Successful native
trace/benchmark diagnostics exit 0; a proof mismatch aborts the benchmark.

**413 tests passed.** Current augmented public results: authorization 32/32;
published status agreement 16/32 (16 abstentions); exact rows/sequences 2/32;
78/193 step recall with precision 1.0; field agreement 522/1,351. The 134 diagnostic
candidate steps are separate and are not predictions. Hidden/full-dataset accuracy
and semantic extraction recall remain unmeasured. Full details and historical
measurements are in code/evaluation/evaluation_report.md.

## Model configuration and usage

Ordinary supported requests use native parsing, including Japanese/Korean
authorization and negation. The optional provider adapter is selective: only
unresolved interpretation can request a model. Calls default to zero. The offline
evaluation path disables providers entirely. Actual repair runs used 0 provider
calls, 0 input/output tokens and USD0 model-service cost, excluding development
session usage and local compute. No final prediction-producing usage run exists.

Optional provider/model configuration uses OPENAI_API_KEY and GHOSTTRACE_MODEL,
kept outside Git and transcripts. --max-model-calls requires an explicit extraction
mode and an opt-in budget (maximum 64 attempts, at most 3 per task). No provider
or model was selected or called in this repair. Prices are never assumed;
optional verified per-million rates use GHOSTTRACE_INPUT_USD_PER_MILLION,
GHOSTTRACE_OUTPUT_USD_PER_MILLION and GHOSTTRACE_CACHED_INPUT_USD_PER_MILLION.
Unknown usage/pricing stays unknown. See code/evaluation/usage_report.md.

## Evidence boundaries

The official canonical identity table's updated_at anchors identity validity;
it does not become a capture timestamp or a citeable record-state observation.
Undated generic snapshots remain provisional. All record-state observations still
need both availability and observation clocks at/before audit_at. Future captures,
reported workflow results, resource-name suffixes and public labels cannot supply
missing identity/state proof.

Finite-corpus coverage requires accounted input sources, resolved identity,
linked resource state and interpretation of matching documents. It does not claim
knowledge outside the supplied dataset. Unknown shared-context, retention,
attachment ownership, restore or flow facts remain blockers. Engineering choices
and the current risk register are in DECISIONS.md. The authentic transcript is
log.txt; no submission archive or upload has been produced.
