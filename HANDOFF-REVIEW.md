# Antigravity handoff review — 25 October 2026

Reviewed commit: `fc6909251bc7b74b3c0061376d81276638a820a2` on merged `main` in the designated GhostData repository.
This is an independent local review, not an organizer evaluation. The attached
Antigravity report is the handoff source; its readiness claims were tested rather
than accepted as proof.

## Verified

- GitHub PR1 merged the Antigravity branch; local main was fast-forwarded from
  399eba8 to fc69092. Official dataset/, AGENTS.md and problem_statement.md are
  unchanged between these commits.
- The merged source suite passes **413 tests in21.42 seconds**.
- A fresh, isolated full audit processes518 requests and reports155 COMPLETE,
  353 INCOMPLETE and10 NOT_APPLICABLE, with0 unresolved and no ingestion errors.
  These are internally computed decisions, not verified hidden-label accuracy.
- Public development evaluation reproduces25/32 publishable correct statuses,
  **5/32 exact rows/sequences**,137/142 step precision,137/193 step recall,
  F1=0.817910, and914/1386 field agreement. Seven sample cases still abstain;
  the sample command exits1. These labels were already inspected during development.
- submission/output.csv has518 correct unique request rows and passes the existing
  structural/citation-metadata validator. That validator explicitly reports
  `semantic_support=NOT_CHECKED`.
- code.zip contains90 entries, required run/report files, no duplicate names and
  none of the checked forbidden dataset/cache/repository directories. The only
  byte mismatch with main is obligations.py line endings; normalized source is
  identical. This is not a stale-logic finding or a comprehensive secret audit.
- All inspection runs make0 provider calls, consume0 provider tokens and report
  USD0 model-service cost. Development-session and local-compute cost are excluded.

## Confirmed correctness blockers

1. **Exclusive attachment ownership is assumed from presence.**
   `code/ghosttrace/policy/obligations.py:49` makes the sole-subject condition true
   from any presence/scan fact. A synthetic attachment with only the subject's
   email and no sole_subject assertion produces REPORT_REMAINING_RECORD,
   DELETE_RECORD and VERIFY_RECORD_ABSENT. Presence or a matching identifier
   does not establish that another subject is absent. This can authorize an
   unsupported deletion under the supplied conditional rule.
2. **Missing policy facts become true.**
   The retention branch at obligations.py:69 accepts missing retention bounds;
   the legal-hold branch at:90 treats presence as active hold. Minimal synthetic
   records lacking those conditions receive COMPLETE with VERIFY_RECORD_PRESENT.
   Backup handling at:252 also treats unknown restore permission as allowed.
   Conservative proposed precautions and evidence-backed state must be distinct.
3. **Document adapters invent IDs and cleared fields.**
   `code/ghosttrace/extract/business.py:75` constructs export IDs from statement
   suffixes;:78 constructs tombstone IDs from user suffixes;:81 constructs object
   IDs from filename suffixes. No explicit resource mapping is required. In a
   synthetic panel containing only `Production workspace` and `user_913`, the
   adapter emits `tombstone_913`, account_status=deleted and null name/email/phone/
   hash fields. Another panel with only a storage heading and a filename emits
   object_842 with sole_subject=true. These are fabricated observations, despite
   carrying a source citation. Unmentioned fields cannot prove redaction.
4. **Generic UI words determine process state.**
   business.py:105 detects Healthy/Continuous/Active anywhere in the panel and
   sets enabled and scheduler_registered; absence of those words sets both false.
   This does not bind status to a specific connector or establish its scheduler.
   A synthetic Disconnected panel emits scheduler_registered=false without any
   scheduler evidence. Missing state must remain unknown.
5. **Packaging validation does not establish readiness.**
   `scripts/package.py` checks row count/sort/status/JSON-array shape but does not
   compare case IDs with the request set, enforce the full seven-field operation
   contract, or verify semantic proof. Its unconditional readiness message is
   stronger than these checks support. It uses asserts, which optimization can
   disable. Existing output passes the fuller validator, but the packaging gate
   itself is insufficient.

## Handoff state and next work

The code has genuine OCR/catalog improvements, and execution is reproducible.
**The blanket claim that all phases are fully verified/submission-ready is not
supported.** Zero internal unresolved cases partly results from the permissive
fallbacks above; it is not evidence that the missing conditions were recovered.
The report's statement of zero false-positive steps also conflicts with137/142
precision (five nonmatching predicted steps).

The next repair should retain the verified OCR/catalog fixes, remove invented
resource/state/policy assumptions, add adversarial regression cases, rerun the
complete public diff and full-dataset gate, then update reports and package only
from that verified source. Public case gaps must be separated from interpretation
errors; no numeric-ID shortcuts or future evidence should fill them.

Earlier Codex edits were preserved locally, without reapplying them to main, in
stash commit `569016ae1ab137511cab88551be761b4f1621384`, named
`codex/pre-antigravity-handoff-preserved-2026-10-25`. They include the additional
27 regression cases from the interrupted work; the merged branch has413 tests,
not that earlier working tree's440. Source fixes are not part of this inspection.

The root output.csv is ignored/untracked and absent after a fresh checkout;
submission/output.csv is tracked. Running the documented full command is required
to recreate the root artifact. README and EVIDENCE-GAPS still show older375/143
figures, while newer report headings declare readiness; these need reconciliation.

Private reproduction outputs and counterexamples are retained under ignored
`.ghosttrace/handoff-*`; inspection used a separate exported main snapshot, with
no paid calls, source edits, dataset modifications or replacement of the tracked
submission bundle.

## Fresh publication check

A fresh isolated `python -B code/main.py --run --with-extraction` exits0,
publishes518 rows and produces an identical parsed CSV to submission/output.csv
(zero differing cases). Raw bytes differ in serialization/line endings; no
semantic output drift was found. The full proof fingerprint is
`f44582c059ce1710232ee8525d16665ba39398009d2edf81d74e910f1a877954`.
The submitted CSV SHA-256 is
`5cfdd86eb54a26585ad9f2565d212e455c0066e8ed049f164623f5352ff216c9`.
