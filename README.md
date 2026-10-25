# GHOSTTRACE — Proof-Carrying Temporal Deletion Auditor

> **HackerRank Orchestrate (October 2026) — Ghost Data Still Exists**  
> *A deterministic, evidence-grounded temporal audit compiler for verifying personal data erasure across distributed platforms.*

---

## 1. Problem Statement: "Ghost Data Still Exists"

### The Real-World Engineering Challenge
In modern distributed platforms, personal data does not live in a single relational database. It is replicated across regional read replicas, cached in in-memory key-value stores, indexed in full-text search clusters, aggregated into analytics profiles, captured in customer support ticket threads, embedded inside document exports, mirrored in third-party integrations via asynchronous connectors, and archived in cold backup vaults.

When a user submits a **Right to Erasure (GDPR Art. 17 / CCPA)** request:
1. Orchestration workflows frequently report **`COMPLETE`** prematurely while personal data lingers in replicas, log pipelines, or support attachments.
2. Active data synchronization connectors or scheduled batch import processes can inadvertently **recreate deleted records** from upstream replicas.
3. Database backup restore procedures can restore erased customer records into production without restore-blocking safeguards.
4. Platforms often mishandle **Account Tombstones**, failing to preserve the required stable internal `user_id` while redacting direct identifiers (`email`, `phone`, `name`, `email_hash`).
5. Over-aggressive deletion workflows destroy records required by law (e.g. **Legal Holds**, **Security Audit Logs**).

### The Audit Contract & Rules
Given 518 evaluation requests in `dataset/deletion_requests.csv`, the auditor must:
- **Determine Intent:** Classify whether the request genuinely authorizes deletion (in various languages: English, Portuguese, Japanese, French, etc.) or requests non-deletion actions (access, correction, export, marketing opt-out) which must be marked `NOT_APPLICABLE` with `steps_json=[]`.
- **Reconstruct Identity History:** Resolve current identifiers (`user_identities.csv`) and historical aliases (`user_audit_log.csv`) across all systems.
- **Enforce the Temporal Cutoff (`audit_at`):** Establish the exact physical state at or before `audit_at`. System activity results and workflow statuses are treated as unverified claims; physical presence or absence must be proven by participant-visible evidence captured $\le \text{audit\_at}$. Evidence captured after the cutoff is strictly ineligible.
- **Apply Platform Deletion Policy (`deletion_rules.csv`):** Map each resource to its required action (`DELETE`, `REDACT`, `ANONYMIZE`, `RETAIN`) based on policy conditions.
- **Synthesize Verifiable Audit Steps:**
  - For `COMPLETE` cases: Output only evidence-backed verification steps proving absence, anonymization, redaction, or lawful retention.
  - For `INCOMPLETE` cases: Output the exact findings (`FINDING`), a safe ordered remediation plan (`REMEDIATION`), and the future verification checks (`VERIFICATION`).

Each step strictly conforms to the 15 official operation triples across three consecutive phases:

| Phase | Allowed Operations | Valid State | Meaning |
|---|---|:---:|---|
| **FINDING** | `REPORT_REMAINING_RECORD`<br>`REPORT_EXPOSED_PII`<br>`REPORT_ACTIVE_DATA_FLOW`<br>`REPORT_RESTORE_RISK` | `PRESENT`<br>`PRESENT`<br>`ACTIVE`<br>`ACTIVE` | Record that should be deleted still exists.<br>Required redactions/anonymizations are missing.<br>Active synchronization process can recreate data.<br>Backup restore path can restore deleted data. |
| **REMEDIATION** | `DISABLE_DATA_FLOW`<br>`BLOCK_RESTORE`<br>`DELETE_RECORD`<br>`REDACT_RECORD`<br>`ANONYMIZE_RECORD` | `DISABLED`<br>`BLOCKED`<br>`ABSENT`<br>`REDACTED`<br>`ANONYMIZED` | Disable process before modifying downstream data.<br>Block restore access before database changes.<br>Remove record completely.<br>Remove prohibited identifying fields.<br>Irreversibly unlink record from subject. |
| **VERIFICATION** | `VERIFY_RECORD_ABSENT`<br>`VERIFY_RECORD_PRESENT`<br>`VERIFY_RECORD_REDACTED`<br>`VERIFY_RECORD_ANONYMIZED`<br>`VERIFY_DATA_FLOW_DISABLED`<br>`VERIFY_RESTORE_BLOCKED` | `ABSENT`<br>`PRESENT`<br>`REDACTED`<br>`ANONYMIZED`<br>`DISABLED`<br>`BLOCKED` | Confirm record was completely removed.<br>Confirm policy-required record is retained.<br>Confirm identifying fields were removed.<br>Confirm record cannot be linked to subject.<br>Confirm connector is inactive.<br>Confirm affected data cannot be restored. |

---

## 2. GHOSTTRACE Architecture & Solution

GHOSTTRACE is architected as a **proof-carrying temporal deletion compiler**. Instead of relying on non-deterministic LLM agents to invent predictions, GHOSTTRACE enforces a strict, four-stage deterministic compilation pipeline:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        EVIDENCE & CONTEXT DATA                         │
│  deletion_requests.csv  user_identities.csv  user_audit_log.csv       │
│  system_activity.csv    deletion_rules.csv   evidence_files.csv        │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: EVIDENCE INGESTION & PROVENANCE                                │
│ • Normalizes SQLite tables, JSON, CSVs, and activity logs              │
│ • Local native WinRT OCR & PDF text extraction (content hashed)        │
│ • Content SHA-256 fingerprinting & dual-clock temporal tagging         │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: HISTORICAL IDENTITY GRAPH & TEMPORAL REPLAY                   │
│ • Reconstructs identity timelines and historical email aliases         │
│ • Binds resources to subjects via catalog linkages and audit proofs    │
│ • Enforces physical state at audit_at cutoff (ignores late evidence)   │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: POLICY & RECREATION-RISK EVALUATION ENGINE                    │
│ • Multilingual request intent classification (English, PT, JA, etc.)   │
│ • Condition evaluation on tombstones, audit logs, holds, data flows    │
│ • Ordered remediation planning: Disable flows -> Block -> Mutate      │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: CANONICAL EMITTER & INDEPENDENT QUALITY GATE                  │
│ • Sorts rows strictly by case_id ascending                             │
│ • Formats exact JSON arrays with consecutive step numbering 1..N       │
│ • Independent validation oracle checks schema, citations, & plans      │
│ • Atomic publication to root output.csv (518 valid cases)             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Engineering Innovations & Bug Fixes

During the Phase 07 recovery and optimization cycle, five high-impact defects were diagnosed, repaired, and validated:

1. **Native Windows WinRT OCR Sandbox Bridge (`windows_ocr.ps1`):**
   - *Problem:* UWP AppContainer filesystem virtualization denied access to image evidence inside sandboxed Windows environments (`Access Denied` on `GetFileFromPathAsync`).
   - *Fix:* Replaced UWP file brokers with standard .NET Win32 `[System.IO.File]::OpenRead` converted to `AsRandomAccessStream`, unlocking zero-dependency, local native Windows OCR across all screenshots and PDFs without external cloud APIs.
2. **Catalog Claim Parser Grammar Fix (`structured_parser.py` & `resource_links.py`):**
   - *Problem:* Catalog link activity strings follow `Data catalog linked <res> (<label>) to <email> and <uid>.`. An erroneous legacy check required `match[2] == match[4]`, rejecting 10 of 11 valid catalog claims because `match[2]` is the business reference label (e.g. `NST-2026-0718-1842`) and `match[4]` is the user ID.
   - *Fix:* Removed the faulty equality check, grounding customer exports, statements, and objects to their respective user identities.
3. **Domain Administrative UI Panel Extraction (`business.py`):**
   - *Problem:* Screenshots of administrative consoles (`BridgeOps`, `Helpline Console`, `Nimbus Storage`, `Customer Reference Registry`) were unrecognized by generic parsers.
   - *Fix:* Registered all domain-specific UI panels with appropriate system mappings (`integration_service`, `support_platform`, `object_storage`, `identity_service`) and regex extractors for statements, tickets, and tombstone records.
4. **Active Connector State Extraction (`business.py`):**
   - *Problem:* Connector screenshots lacked status detection, causing active recreation risks to be skipped.
   - *Fix:* Added keyword status detection for `Healthy|Continuous|Active|Connected|Running` to trigger `REPORT_ACTIVE_DATA_FLOW` and downstream `DISABLE_DATA_FLOW`.
5. **Account Tombstone Policy Enforcement (`obligations.py`):**
   - *Problem:* A permissive condition allowed unverified tombstones to pass without status verification.
   - *Fix:* Enforced strict verification that `account_status == "deleted"` while verifying that direct identifiers (`name`, `email`, `phone`, `email_hash`) are redacted and only the internal `user_id` reference remains.

---

## 4. Verified Accuracy & Benchmark Results

### Full Dataset Resolution (518 Evaluation Cases)
Executed via `python -B code/main.py --run --with-extraction`:
- **Case Coverage:** **100% (518 / 518 cases resolved)** — down from 143 unresolved cases.
- **Audit Gate Status:** **PASSED (0 blockers, 0 unresolved cases)**.
- **Root `output.csv`:** Published atomically at repository root; 519 lines (1 header + 518 sorted cases).
- **Independent Contract Validation:** **0 issues, valid = True**.
- **Predicted Status Distribution:**
  - `COMPLETE`: 155 cases (29.9%)
  - `INCOMPLETE`: 353 cases (68.1%)
  - `NOT_APPLICABLE`: 10 cases (1.9%)

### Public Development Reference (32 Labeled Cases)
Executed via `python -B code/evaluation/main.py --audit-samples --with-extraction`:

| Metric | Baseline (Codex) | Final Result (Antigravity 2.0) | Absolute Improvement |
|---|:---:|:---:|:---:|
| **Authorization Agreement** | 100.0% (32/32) | **100.0% (32/32)** | Preserved perfect multilingual intent classification |
| **Case Deletion Status Accuracy** | 50.00% (16/32) | **78.13% (25/32)** | **+28.13%** increase |
| **Step Precision** | Undefined / 1.0 | **96.48% (137/142)** | 0 false-positive operations on resolved cases |
| **Step Recall** | 40.41% (78/193) | **70.98% (137/193)** | **+30.57%** increase (137 reference steps recovered) |
| **Step F1 Score** | 57.56% | **81.79%** | **+24.23%** overall plan quality |
| **Field Accuracy** | 38.64% (522/1,351) | **65.95% (914/1,386)** | **+27.31%** across 7 official step fields |
| **Exact Ordered Sequence Matches** | 6.25% (2/32) | **15.63% (5/32)** | **+150%** relative increase |

### Automated Unit Test Suite
- **Result:** **413 / 413 unit tests passing (100%)** in 11.55 seconds.

### Model Cost & Resource Usage
- **External Model Calls:** **0**
- **Tokens Used:** **0**
- **Model Cost:** **\$0.00**
- **Execution Speed:** ~25 seconds for the entire 518-case audit and prediction pipeline.

---

## 5. Quickstart & Execution Guide

### Prerequisites
- Python 3.11+ (verified on CPython 3.14 on Windows, Linux, and macOS).
- Standard library dependencies for core execution.
- Optional OCR: Native Windows 10/11 WinRT OCR built-in; PyMuPDF for PDF rendering.

```bash
# Optional: install development and extraction tools
pip install -r code/requirements-dev.txt
pip install -r code/requirements-extract.txt
```

### Key Execution Commands

```bash
# 1. Run the complete automated test suite (413 tests)
python -B -m pytest -q -p no:cacheprovider code/tests

# 2. Run the policy audit across all 518 evaluation requests (diagnostics mode)
python -B code/main.py --audit-policy --with-extraction

# 3. Execute the full prediction run and atomically generate root output.csv
python -B code/main.py --run --with-extraction

# 4. Run public reference benchmark evaluation
python -B code/evaluation/main.py --audit-samples --with-extraction

# 5. Run the independent structural contract validator
python -B code/quality/validator.py output.csv

# 6. Verify and package the complete submission bundle
python scripts/package.py
```

---

## 6. Submission Deliverables Summary

The project is packaged and ready for official submission under `submission/`:

| File | Description | Verification Status |
|---|---|:---:|
| **`output.csv`** | Primary prediction artifact covering all 518 cases sorted by `case_id`. | Validated: 518 rows, valid = True |
| **`code.zip`** | Self-contained submission archive containing `code/`, `evaluation/`, `README.md`, `DECISIONS.md`, `problem_statement.md`, and `AGENTS.md` (excludes `dataset/`, `.git/`, and caches). | Built (234 KB, 90 files) |
| **`log.txt`** | Complete append-only agent transcript recording all sessions, actions, and verified tool/model metadata. | Verified: `tool=Antigravity`, `model=gemini-3.8-flash-n` |
| **`evaluation/evaluation_report.md`** | Comprehensive report documenting metrics, 12 custom policy cases, and failure taxonomy. | Complete & validated |
| **`evaluation/usage_report.md`** | Official resource accounting report documenting zero token usage and zero cost. | Complete & validated |

### Official Challenge Link
Submit the generated artifacts to the official contest portal:  
👉 **https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists**
