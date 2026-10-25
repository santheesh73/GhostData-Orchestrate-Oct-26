# GHOSTTRACE — Proof-carrying deletion auditor

For each of the 518 deletion requests, GhostTrace resolves current and historical identifiers, replays evidence to `audit_at`, applies `deletion_rules.csv`, and emits contract-exact `steps_json`. Its pipeline is deterministic: no LLM invents operations or evidence IDs, and the final run makes 0 model calls ($0). Where supplied facts are incomplete, the final prediction mode uses the defaults disclosed below.

## Results

Public sample set: these labels were inspected during development, so this is not a held-out score.

| Metric | Value |
|---|---|
| Status accuracy | 32/32 |
| Exact rows | 9/32 |
| Step precision | 98.14% |
| Step recall | 158/193 |
| Full run | 518/518 rows, contract-valid |
| Tests | 542 passing |

Hidden-set accuracy is not measured.

## Architecture

- Ingest (CSV/JSON/SQL/logs; PDF/image text capture with OCR);
- Resolve (temporal identity graph, replay to `audit_at`, conflict resolution);
- Policy & risk (rules, retention, tombstones, data flows, restore risks);
- Emit (operation mapping, canonical ordering, evidence-ID contract);
- Validate (independent contract validator).

Implementation modules: `code/ghosttrace/`.

## Key engineering decisions

- Reported statuses are treated as claims, rather than proof of resulting state.
- Verification covers every established relevant resource, including compliant resources that need no remediation.
- INCOMPLETE remediation and verification steps use `evidence_id: ""`.
- Sample-backed defaults handle unknown retention, ownership and archive-existence conditions without blocking publication.
- Account-absence checks require evidence from the request time onward; earlier negative lookups do not establish current absence.
- No case or resource IDs are hardcoded in prediction rules.

## How to run

Place the supplied `dataset/` beside `code/`. OCR requires Windows OCR or Tesseract.

- Setup: `pip install -r code/requirements-dev.txt -r code/requirements-extract.txt`
- Full run: `python -B code/main.py --run --with-extraction`
- Sample eval: `python -B code/evaluation/main.py --audit-samples --with-extraction`
- Trace: `python -B code/evaluation/main.py --trace-case case_20 --with-extraction`
- Tests: `python -B -m pytest -q -p no:cacheprovider code/tests`

## Evaluation & cost

[Evaluation report](evaluation/evaluation_report.md): measured accuracy, custom cases, failures and improvements.

[Usage report](evaluation/usage_report.md): final-run usage and cost, with 0 model calls ($0).

## Known limitations

- Missing reference steps remain: a 35/193 recall gap.
- Defaults substitute for unsupplied retention, ownership and archive facts; they are assumptions, not recovered evidence.
- OCR-dependent evidence can be missed or misread.
