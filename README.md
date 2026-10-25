# GHOSTTRACE — current recovery status

**NOT READY — CRITICAL BLOCKERS REMAIN.** Known unsafe document/policy defaults
were repaired.503 tests pass;278/518 requests resolve and240 remain unknown.
Public development agreement is16/32 statuses and1/32 exact rows. These are not
hidden accuracy measurements. No new corrected final output or bundle is claimed.

## Setup and run

Python3.11+; verified on Windows CPython3.14.3. Core uses the standard library.
Optional document dependencies are pinned in code/requirements-extract.txt;
tests use code/requirements-dev.txt. They were already installed locally; no new
installation was needed. Native Windows OCR uses the preserved Win32 stream
bridge. Other platforms require Tesseract/English data and are unverified here.

```text
python -m pip install -r code/requirements-extract.txt
python -m pip install -r code/requirements-dev.txt
python -B code/main.py --audit-policy --with-extraction
python -B code/main.py --run --with-extraction
python -B -m pytest -q -p no:cacheprovider code/tests
python -B code/evaluation/main.py --audit-samples --with-extraction
python -B scripts/package.py --structural-only
python -B scripts/package.py --check-only
```

Supply the unchanged participant dataset under dataset/. Do not use organizer
files. --run attempts root output.csv only for all518 official requests passing
proof and full-contract checks. Exit3 blocks publication and preserves any older
output. Existing root output/submission/ artifacts are the historical unsafe
baseline, not regenerated/certified corrected predictions. Do not submit them as
this recovery's result. Imperfect public comparison exits1.

The package script uses release-files.json, the independent output oracle and a
fresh source-grounded audit comparison. --structural-only is diagnostic; it
cannot build a release. --check-only currently blocks. When all gates pass,
`python -B scripts/package.py --out submission-verified` builds a NEW directory
and manifest; existing bundles are never overwritten. It does not upload anything.

Provider calls default tozero. Optional OPENAI_API_KEY/GHOSTTRACE_MODEL values
belong in local environment only; no paid run was approved or used. The offline
evaluator disables providers. All recovery provider tokens/cost are0, excluding
local compute and development sessions. Cache/diagnostics stay in .ghosttrace/.

DESIGN.md describes actual stages and uncertainty; INTERVIEW.md has preparation
notes and constant provenance. Canonical current evaluation/usage reports are
under code/evaluation/ and mirrored at evaluation/. RECOVERY-REPORT.md gives the
phase matrix and release verdict. evaluation/recovery_blockers.json identifies
every affected case/resource. Earlier reports and claims are explicitly historical
under evaluation/history/ and Git history; PHASE-AUDIT/HANDOFF-REVIEW describe the
pre-repair baseline. Official data and authentic append-only log.txt are intact.

Before final trace packaging, finish sessions and quit the tools as directed by
agent_trace_instructions.md. This active Codex trace cannot yet be finalized.
Project-matching Antigravity traces were located, but no complete reviewed multi-
harness trace archive is claimed. No external submission occurred.
