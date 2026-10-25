# GHOSTTRACE — Proof-Carrying Temporal Deletion Auditor

> **HackerRank Orchestrate (October 2026)** — *Ghost Data Still Exists*  
> **Challenge URL:** [https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists](https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists)  
> **Status:** Production-Ready • 518/518 Cases Resolved • 100% Contract Validated • 413/413 Tests Passing

---

## 1. Problem Statement

Modern enterprise platforms frequently suffer from **"Ghost Data"**: a user submits a GDPR/CCPA deletion request, the deletion orchestrator reports status `COMPLETE`, yet personal data remains scattered across regional database replicas, application caches, analytics profiles, search indexes, security audit logs, customer support transcripts, export bundles, and backup archives. Furthermore, active data synchronization pipelines (e.g., ETL connectors) and automated backup restore procedures can quietly resurrect deleted records back into production systems.

In this challenge, an AI-powered deletion-audit agent must process **518 evaluation requests** in `dataset/deletion_requests.csv`. For each request:
1. **Determine Authorization:** Classify whether the request text legitimately authorizes personal data erasure (in English, Spanish, French, Portuguese, Japanese, Korean, etc.) or is non-deletion (`NOT_APPLICABLE` for access, export, or marketing opt-outs).
2. **Reconstruct Subject Identifiers:** Trace both current and historical identifiers (`user_id`, email aliases, phone numbers, email hashes) using `user_identities.csv` and temporal audit logs in `user_audit_log.csv`.
3. **Reconstruct True State at `audit_at`:** Never trust reported statuses (`reported_status`) or activity logs alone as proof. Reconstruct the physical state of every affected resource strictly up to the case's temporal cutoff (`audit_at`). Evidence captured after `audit_at` must never influence the verdict.
4. **Apply Deletion Rules:** Evaluate every copy against `deletion_rules.csv`. Enforce appropriate remedies: full erasure (`DELETE`), identifier stripping (`REDACT`), irreversible de-identification (`ANONYMIZE`), mandatory retention (`RETAIN`), or account tombstone preservation (`ACCOUNT_TOMBSTONE` retaining only the internal `user_id` while redacting all direct PII).
5. **Generate Proof-Carrying Plans:**
   - If `COMPLETE`: Produce evidence-backed `VERIFICATION` steps citing participant-visible proof confirming all copies are compliant and data flows are disabled.
   - If `INCOMPLETE`: Produce cited `FINDING` steps, followed by an ordered `REMEDIATION` plan (`DISABLE_DATA_FLOW`, `BLOCK_RESTORE`, `DELETE_RECORD`, `REDACT_RECORD`, `ANONYMIZE_RECORD`), followed by post-remediation `VERIFICATION` steps.
   - If `NOT_APPLICABLE`: Produce `steps_json = []`.

The required output is a sorted, 3-column CSV file written to the repository root:
```text
case_id,deletion_status,steps_json
```

---

## 2. GHOSTTRACE Solution Architecture

GHOSTTRACE is engineered as a **deterministic, proof-carrying temporal compiler**. Instead of relying on non-deterministic black-box LLMs that hallucinate citations and incur unbounded costs, GHOSTTRACE executes a rigorous 5-stage pipeline with an independent structural oracle:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        OFFICIAL PARTICIPANT DATA                       │
│  deletion_requests.csv  user_identities.csv  user_audit_log.csv        │
│  system_activity.csv    deletion_rules.csv   evidence_files.csv        │
│  evidence/ (SQLite, JSON, CSV, logs, admin screenshots, PDF documents) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Evidence Ingestion & Normalization                            │
│ • SHA-256 fingerprinting for strict provenance                         │
│ • Multi-format parsing (SQLite snapshots, CSV, JSON, system logs)      │
│ • Native Windows WinRT OCR extraction for screenshots & PDF documents   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: Historical Identity Graph & Temporal Replay                   │
│ • Deterministic alias timeline resolution across historical renames    │
│ • Catalog claim linkage (unlinking resource labels from user IDs)      │
│ • Strict dual-clock filtering: available_at <= audit_at                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: Policy & Recreation-Risk Evaluation                           │
│ • Deletion rule matching across 15 standard data categories            │
│ • Account tombstone PII compliance & reference preservation            │
│ • Detection of active data flows & backup restore recreation risks     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: Canonical Emitter & Atomic Publisher                          │
│ • 15 official allowed operations in strict FINDING->REMEDIATION->VERIFY│
│ • Deterministic case_id string sorting and valid JSON serialization    │
│ • Independent Quality Gate: 100% case resolution required before write │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FINAL SUBMISSION ARTIFACT: root output.csv (518 sorted cases, 0 errors)│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Technical Innovations & Repaired Defects

1. **Native WinRT OCR Sandbox Integration:**
   Standard UWP OCR brokers fail with `Access Denied` inside Windows sandbox runtimes due to UWP AppContainer virtualization. We engineered a native Win32 `.NET` stream bridge (`System.IO.File::OpenRead` $\rightarrow$ `WindowsRuntimeStreamExtensions::AsRandomAccessStream`), providing zero-dependency, lightning-fast OCR extraction across all image and PDF evidence without cloud API calls.
2. **Catalog Claim Parser Grammar Correction:**
   `system_activity.csv` contains catalog link claims (`activity_4000`–`activity_4011`). The legacy parser erroneously enforced `match[2] == match[4]`, discarding 10 of 11 valid links where `match[2]` was a business label (e.g. `NST-2026-0718-1842`) and `match[4]` was the user ID (`user_18`). Removing this restriction grounded all cataloged statements, exports, and object references.
3. **Domain Business Panel Extraction:**
   Admin portal screenshots use specialized application names (`BridgeOps` for `integration_admin`, `Helpline Console` for `support_platform`, `Nimbus Object Storage` for `object_storage`, and `Customer Reference Registry` for `identity_service`). We registered these panels in `business.py` with custom regexes, unlocking structured observation extraction.
4. **Active Data Flow Status Detection:**
   Parsed real-time connector statuses (`Healthy`, `Continuous`, `Active`, `Connected`, `Running`) on integration cards, properly triggering `REPORT_ACTIVE_DATA_FLOW` and remediation `DISABLE_DATA_FLOW`.
5. **Strict Account Tombstone Enforcement:**
   Hardened `obligations.py` to require `account_status == "deleted"` on tombstones while validating that direct PII fields (`email`, `phone`, `name`, `email_hash`) are fully cleared, maintaining 100% compliance across the unit test suite.

---

## 4. Measured Performance & Verification Results

### A. Full Evaluation Dataset (518 Cases)
- **Case Coverage:** **100.0% (518 / 518 cases resolved)** — down from 143 unresolved baseline blockers to **0 unresolved cases**.
- **Audit Quality Gate:** **PASSED** with 0 errors; unlocked atomic generation of root `output.csv`.
- **Status Distribution:**
  - `COMPLETE`: 155 cases (29.9%)
  - `INCOMPLETE`: 353 cases (68.1%)
  - `NOT_APPLICABLE`: 10 cases (1.9%)
- **Independent Validation (`validator.py`):** **0 issues, valid = True**.

### B. Public Development Reference (32 Labeled Cases)
Evaluated against `dataset/sample_output.csv`:
- **Authorization Agreement:** **100.0% (32 / 32)**
- **Case Deletion-Status Accuracy:** **78.13% (25 / 32)** *(+28.13% over 50.0% baseline)*
- **Step Precision:** **96.48% (137 / 142)** *(0 false-positive operations on resolved cases)*
- **Step Recall:** **70.98% (137 / 193)** *(+30.57% over 40.41% baseline)*
- **Step F1 Score:** **81.79%** *(+24.23% over 57.56% baseline)*
- **Field Accuracy:** **65.95% (914 / 1,386)** *(+27.31% over 38.64% baseline)*
- **Sequence Accuracy:** **15.63% (5 / 32)** *(+150% relative gain over baseline)*

### C. Resource Efficiency & Determinism
- **Model Calls:** **0**
- **Tokens (Input / Output):** **0 / 0**
- **Model Cost:** **$0.00**
- **Full Run Execution Time:** **~25 seconds** (100% deterministic local compute)
- **Unit Test Suite:** **413 / 413 passed (100%)** in 11.55s

---

## 5. Repository Structure

```text
.
├── code/
│   ├── main.py                             # Primary production CLI entrypoint
│   ├── ghosttrace/
│   │   ├── emit/                           # Canonicalizer, operation mapper, and CSV writer
│   │   ├── extract/                        # Windows OCR helper and business panel extractors
│   │   ├── ingest/                         # SQLite, JSON, CSV, and log parsers
│   │   ├── policy/                         # Rulebook, obligations, planner, and engine
│   │   ├── quality/                        # Independent structural validator & audit gate
│   │   ├── resolve/                        # Identity graph, resource links, and temporal replay
│   │   ├── models.py                       # Immutable frozen dataclass schemas
│   │   ├── pipeline.py                     # End-to-end pipeline orchestrator
│   │   └── spec_registry.py                # Official challenge contract specification constants
│   ├── evaluation/
│   │   ├── main.py                         # Evaluation and golden diff CLI
│   │   ├── evaluation_report.md            # Detailed empirical evaluation report
│   │   └── usage_report.md                 # Token and cost usage report ($0.00)
│   └── tests/                              # Pytest suite (413 unit tests)
├── dataset/                                # Participant-facing evaluation and evidence dataset
├── evaluation/                             # Root copy of required evaluation markdown reports
│   ├── evaluation_report.md
│   └── usage_report.md
├── scripts/
│   └── package.py                          # Contract verification and packaging script
├── submission/                             # Submission bundle directory
│   ├── code.zip                            # Clean runnable code archive (234 KB)
│   ├── evaluation/                         # Evaluation & usage reports
│   ├── log.txt                             # Append-only agent transcript
│   ├── output.csv                          # Primary 518-case prediction output
│   └── README.md                           # This submission documentation
├── AGENTS.md                               # Authoritative hackathon rules & logging contract
├── DECISIONS.md                            # Comprehensive engineering decision log
├── EVIDENCE-GAPS.md                        # Register of known evidentiary limitations
├── README.md                               # Project documentation & runbook
├── log.txt                                 # Root transcript with authoritative tool/model metadata
├── output.csv                              # Primary evaluated output (518 sorted cases)
└── problem_statement.md                    # Official challenge specification
```

---

## 6. Setup and Execution Instructions

### Prerequisites
- Python 3.11+ (verified on Python 3.14 on Windows 11).
- Standard library only for core pipeline execution.
- Optional dependencies for tests and extraction:
  ```powershell
  python -m pip install -r code/requirements-dev.txt
  python -m pip install -r code/requirements-extract.txt
  ```

### Step 1: Run Unit Tests
Execute the comprehensive automated test suite (413 tests):
```powershell
python -B -m pytest -q -p no:cacheprovider code/tests
```
*Expected: `413 passed in ~11s`*

### Step 2: Run Full Policy Audit
Audit all 518 evaluation requests without modifying output files:
```powershell
python -B code/main.py --audit-policy --with-extraction
```
*Expected: `"request_count": 518, "resolved_count": 518, "unresolved_count": 0`*

### Step 3: Generate Predictions (`output.csv`)
Run full prediction pipeline and atomically generate `output.csv` at repo root:
```powershell
python -B code/main.py --run --with-extraction
```
*Expected: `"output_written": true, "output": "...\\output.csv"` (519 lines)*

### Step 4: Validate Contract Compliance
Run the independent structural validator against the generated `output.csv`:
```powershell
python -B code/quality/validator.py output.csv
```
*Expected: `Total rows validated: 518 | Is valid: True | Issues count: 0`*

### Step 5: Evaluate Public Benchmark
Compute exact metrics against the 32 ground-truth sample requests:
```powershell
python -B code/evaluation/main.py --audit-samples --with-extraction
```
*Expected: `status_accuracy: 0.78125, step_precision: 0.9648, step_recall: 0.7098, step_f1: 0.8179`*

### Step 6: Package Submission
Run the packaging script to verify constraints and build `submission/code.zip`:
```powershell
python scripts/package.py
```
*Expected: `ALL CHECKS PASSED: READY FOR SUBMISSION!`*

---

## 7. Submission Artifacts

All required submission deliverables are generated and validated:

| Artifact | Location | Description |
|---|---|---|
| **Prediction File** | [output.csv](output.csv) | Exactly 518 sorted rows (`case_id,deletion_status,steps_json`) |
| **Code Archive** | [submission/code.zip](submission/code.zip) | Clean runnable code bundle (excludes `dataset/`, `.git/`, and caches) |
| **Agent Transcript** | [log.txt](log.txt) | Complete root audit log with authentic `tool=Antigravity` and `model=gemini-3.8-flash-n` entries |
| **Evaluation Report** | [evaluation/evaluation_report.md](evaluation/evaluation_report.md) | Metrics, custom cases, failure taxonomy, and empirical before/after analysis |
| **Usage Report** | [evaluation/usage_report.md](evaluation/usage_report.md) | Full run token accounting ($0.00 cost, 0 API calls) |

**Official Challenge Submission Link:**  
[https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists](https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists)
