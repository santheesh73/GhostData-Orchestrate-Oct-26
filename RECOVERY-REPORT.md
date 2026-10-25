> HISTORICAL RECOVERY CHECKPOINT (d302f17). Current Phase06B measurements and release status are in PHASE06B-REPORT.md. This earlier report is preserved.

# GHOSTTRACE final recovery engineering report — 25 October 2026

## A. Executive summary

**NOT READY — CRITICAL BLOCKERS REMAIN.** The documented unsafe source paths were
repaired and503 tests pass. The corrected engine resolves278/518 requests and
blocks240, preserving UNKNOWN instead of fabricating policy/document facts.
The root historical CSV and submission/ bundle remain preserved but are not a
corrected approved release. No paid model call or external submission occurred.

## B. Phase00–07 acceptance matrix

| Phase | Initial state | Repairs/evidence | Final disposition |
|---|---|---|---|
|00|Conflicting living reports|Current README/gaps/evaluation/usage reconciled; historical text preserved|Complete for current blocked-state reporting|
|01|Runnable structurally valid baseline|Independent full oracle retained; writer preservation verified; contract tests pass|Contract implementation complete; semantic publication blocked downstream|
|02|Parsers work; catalog fix valid|Catalog/OCR retained; causal log query metadata bound by file/service/instance/trace/operation/time|Supported ingestion complete; semantic recall not certified|
|03|Unsupported categories/archive presence; owner field ignored|Removed prefix inference; separated permission/presence; explicit competing owner/list controls|Known defects repaired/tested; required source links/state remain open|
|04|Missing conditions converted to facts|Explicit retention/hold/sole/shared conditions; deleted-only tombstones; excerpt guards|Known defects repaired/tested; unknown conditions block case acceptance|
|05|Invented IDs/nulls/states|Literal row/header/labeled extraction; no guessed nulls/sole ownership/scheduler; field quotes retained|Known fabrication paths repaired; interpretation/coverage incomplete|
|06|413 tests, incomplete public plans|503 pass; full/candidate/public metrics; cached/reference proof equality; every case disposition recorded|Verification tools complete; quality/coverage gate not passed|
|07|Bundle built with weak checks|Explicit inventory, full-contract oracle, fresh semantic compare, hashes, no-overwrite staging, optimized-Python check|Release blocked; no corrected final bundle claimed|

## C. Root causes and corrected behavior

Presence is not exclusive ownership, retention validity or active legal hold.
These conditions now require explicit fields/intervals or defensible content
interpretation. Inactive is not deleted. Uninterpreted excerpts/bodies/notes do
not become proof of cleared identifiers. A complete narrow grammar can interpret
generic support summaries; it cannot accept names/numbers/addresses/unknown words.

Statements/user references/filenames do not supply new resource IDs. Documents
use literal or explicitly bound rows, preserve missing fields as missing, and
retain the source/adapter/locators/validated field quotations. A support ticket
reference cannot stand in for an attachment ID. Generic UI status words cannot
supply a scheduler state. Native OCR and actual catalog grammar fixes remain.

Restore authorization records permission only; existence/readback and effective
restore controls remain distinct. Category prefixes no longer substitute for
schemas. owner_user_id and scalar reference lists no longer silently disappear
from competing ownership. Unknown cases cannot pass the proof/publication gate.

## D. Adversarial results

Before repairs,20 of30 new recovery controls failed (10 passed). Final full suite:
**503 passed in26.04s**,90 more than baseline. New files contain43 recovery,
27 recovered reader and20 packaging cases. Positive controls remain alongside
negative and conflicting cases. Existing policy/form/ingestion tests were updated
to require explicit archive state, distinguish an attachment ID from a support
ticket, and preserve an existing output rather than assume it cannot exist.
Tests were not weakened to accept fabricated facts.

Covered: all requested fabricated ID/null/status/sole/scheduler examples; explicit
positive labeled tombstones/objects; missing/false/conflicting ownership/hold/
retention; unknown excerpts; archive authorization; current/historical clocks;
row mismatches; file/instance/trace boundaries; malformed contract/package inputs.
Full reproduction outputs are retained under ignored .ghosttrace/recovery/ and
authentic Codex tool traces. No held-out or official score is inferred.

## E. Modified files and functions

- extract/business.py project_document/_ui_records/enrich_business_documents:
  literal source-bounded extraction, validated fields, temporal lexicons.
- extract/documents.py local_records and validation.py validate_records:
  explicit underscore/space field labels retain equivalent quote validation.
- ingest/log_parser.py parse_log: logical service alias plus causal query context.
- ingest/normalization.py identifiers_from and resolve/signals.py signals:
  explicit owner IDs and competing scalar references.
- resolve/temporal_replay.py extract_facts: typed direct readbacks, separate archive
  and restore permission; no prefix state classification.
- policy/rulebook.py category, obligations.py condition/pii/assess, facts.py project:
  no unknown-to-true policy defaults, explicit context/retention and full text guard.
- scripts/package.py: validate_output/member_snapshot/semantic_check/build_package:
  explicit errors, full oracle, current-source compare, atomic new bundle/hashes.
- Tests, release-files.json and documentation: acceptance evidence and artifact scope.

Exact changed/new path inventory at report generation:

- DECISIONS.md
- DESIGN.md
- EVIDENCE-GAPS.md
- HANDOFF-REVIEW.md
- INTERVIEW.md
- PHASE-AUDIT.md
- README.md
- code/evaluation/evaluation_report.md
- code/evaluation/usage_report.md
- code/ghosttrace/extract/business.py
- code/ghosttrace/extract/documents.py
- code/ghosttrace/extract/validation.py
- code/ghosttrace/ingest/log_parser.py
- code/ghosttrace/ingest/normalization.py
- code/ghosttrace/policy/facts.py
- code/ghosttrace/policy/obligations.py
- code/ghosttrace/policy/rulebook.py
- code/ghosttrace/resolve/signals.py
- code/ghosttrace/resolve/temporal_replay.py
- code/tests/test_business_readbacks.py
- code/tests/test_corpus.py
- code/tests/test_packaging.py
- code/tests/test_phase06_repairs.py
- code/tests/test_policy.py
- code/tests/test_recovery.py
- evaluation/evaluation_report.md
- evaluation/history/EVIDENCE-GAPS-9f534ca.md
- evaluation/history/README-9f534ca.md
- evaluation/history/evaluation-report-9f534ca.md
- evaluation/history/usage-report-9f534ca.md
- evaluation/recovery_blockers.json
- evaluation/usage_report.md
- release-files.json
- scripts/package.py

## F. Evaluation comparison

| Metric | Historical baseline | Corrected final | Change |
|---|---:|---:|---|
|Tests|413|503|+90|
|Internal resolved|518/518|278/518|240 now honestly blocked|
|Status agreement|25/32|16/32|-9|
|Exact rows/sequences|5/32|1/32|-4|
|Step precision|137/142|73/73|96.48% to100%|
|Step recall|137/193|73/193|70.98% to37.82%|
|Field agreement|914/1386|481/1351|65.95% to35.60%|
|Abstentions|7|16|+9|

Current full statuses:88 COMPLETE,180 INCOMPLETE,10 NOT_APPLICABLE,240 unresolved.
Public authorization32/32; F1=54.89%. Safety fixes reduced coverage/recall; this is
not represented as overall accuracy improvement. Candidates are separate from
published steps. All32 public case dispositions and failure causes are in the
canonical evaluation report; evaluation/recovery_public_cases.json contains
per-case taxonomy tags, uncertainties and separate candidate/reference steps.
These are reference differences, not authorization to emit missing operations.
Hidden accuracy/semantic recall remain NOT MEASURED.
Full observed native runtime was55.277s with competing
verification processes; this is not a controlled speed benchmark. Provider usage
and service cost are0, excluding development sessions and local compute.

## G. Source integrity

Official dataset/, AGENTS.md and problem_statement.md are unchanged from9f534ca.
Only participant-facing runtime inputs were used; public labels were opened by
the evaluator after inference. No generator/private truth was read. Dataset and
implementation fingerprints are in evaluation/recovery_integrity.json. Stash
569016ae1ab137511cab88551be761b4f1621384 remains preserved; reviewed fragments were
reconciled individually rather than applying it over merged work.

## H. Output validation

- python -B -m pytest -q -p no:cacheprovider code/tests:exit0,503 passed.
- Public comparison in augmented mode:imperfect,exit1;16 publishable cases.
- Full diagnostics:518 processed,240 unresolved; not a complete output.
- python -B code/main.py --run --with-extraction:exit3; historical root
  file preserved=True. No partial root CSV is written.
- Cached/reference full proofs identical=True.
  Audit SHA256:d6bf711ea6f0e412ee9dc923958979d06844be9ffdb1c8490425c4d6c8cab23b.

## I. Package validation and reproducibility

python -B scripts/package.py --structural-only:exit0 for the historical CSV's
shape/metadata; semantic_support remains NOT_CHECKED and it cannot build.
python -B -O scripts/package.py --check-only:exit1,PACKAGE BLOCKED for240 cases.
Assertions disabled cannot bypass validation. The packager's valid synthetic
staging/hash/inventory tests pass and existing bundles survive rejected builds.

The old code.zip remains unchanged; previous independent inspection found90
members, required reports and no checked forbidden dataset/cache members. It is
historical and does not contain current repairs. No new full prediction-producing
artifact or matching final bundle can be certified while240 cases are unresolved.
The explicit prospective inventory is release-files.json. A clean corrected-source
blocked-run reproduction is recorded after the source checkpoint below; it cannot
be represented as a successful518-row release reproduction. No unnecessary
packages were installed merely to repeat an already available environment.

## J. Documentation and trace reconciliation

Current README/gaps/evaluation/usage documents report the blocked corrected run.
Historical copies preserve prior results verbatim under evaluation/history/;
earlier phase/handoff audits are labeled historical, and DECISIONS.md appends
current outcomes without erasing prior claims. No successful corrected final-run
usage is claimed. DESIGN.md documents actual behavior; INTERVIEW.md gives honest
preparation and constant provenance, not a fabricated interview transcript.

agent_trace_instructions.md requires finishing/quitting sessions before export.
This Codex session is active, so its complete final trace cannot yet be packaged.
Three project-matching Antigravity transcript paths were located; no unrelated
traces or authentication/configuration files were copied. No complete reviewed
multi-harness agent-trace.zip is claimed. Final export/review remains required.

## K. Skills actually used

hackerrank-orchestrate-evidence; hackerrank-orchestrate-design;
orchestrate-test-fix; orchestrate-submit; hackerrank-orchestrate-package;
orchestrate-interview. Applied source/proof boundaries, regression/diff controls,
release checks, explicit inventory and honest technical explanations. No skill
installation, framework, agent swarm, paid calls or external upload occurred.

## L. Precise blockers and next evidence requirement

All240 affected evaluation cases, resource IDs and reason codes are in
[evaluation/recovery_blockers.json](evaluation/recovery_blockers.json).
There are337 security-retention scopes,127 shared-context scopes,3 exclusive-
attachment scopes,3 archive-presence scopes,1 legal-hold scope and remaining
link/category/coverage gaps; scopes overlap within cases. Affected operations
include VERIFY_RECORD_PRESENT, REDACT_RECORD/VERIFY_RECORD_REDACTED,
DELETE_RECORD/VERIFY_RECORD_ABSENT and restore verification/planning. They cannot
be asserted without the relevant missing pre-cutoff state or condition.

Missing subject bindings for deidentified/absent records and after-cutoff linking
evidence remain concrete source gaps. Other unknowns may admit further source
interpretation; no blanket impossibility claim is made. Best-effort supported
rows and full diagnostics are preserved privately as resolved-only.json, not a
partial official CSV. The historical all518 candidate is retained for comparison
but remains uncertified. No request to lower evidence safety or buy model access
is necessary to describe these blockers honestly.

## M. Final verdict

NOT READY — CRITICAL BLOCKERS REMAIN

## Final clean-source verification checkpoint

Corrected application source commit:e0e4538f50acc141d460a5cc051cfb3505299cf9.
A new committed-source export with exact unchanged participant evidence bytes
reproduces the same case diagnostics and full proof as the working tree.
`python -B code/main.py --run --with-extraction` exits3;240 unresolved;
88 COMPLETE,180 INCOMPLETE,10 NOT_APPLICABLE; no root output is created.
Observed fresh-cache run81.271s, not a speed benchmark. Existing documented
dependencies were verified (PyMuPDF1.27.2.3,Pillow12.2.0,pytest9.1.1); no clean
machine dependency installation or cross-platform run is claimed.

Clean source snapshot SHA256 (diagnostic export, not a submission code.zip):
`f7d5baef0e98ee6e1ab1a172dec05080557d37095b95a65a1396c3470ae296f3`.
Explicit prospective inventory/secret-pattern scan accepts99 archive members
and the transcript; this is a pattern check, not proof of absence of every possible
secret. No new release archive was built because the semantic gate blocks240.
The actual old bundle and output hashes are in evaluation/recovery_integrity.json.

Additional final evidence files:evaluation/recovery_public_cases.json (all32
public dispositions and diagnostic taxonomy), evaluation/clean_reproduction.json
and updated evaluation/recovery_integrity.json. RECOVERY-REPORT.md is part of the
explicit prospective release inventory. The final documentation commit changes
no application logic relative to the verified source checkpoint.
