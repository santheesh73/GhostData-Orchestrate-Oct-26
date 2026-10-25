# Final submission evaluation — 25 October 2026

Public development reference; previously inspected, not held out. Runtime inference
opens no expected answers and contains no case/resource-ID overrides. Heuristic
policy defaults were explicitly authorized for the final competition prediction.

| Metric | Strict Phase06B | Final prediction |
|---|---:|---:|
|Predicted public cases|16/32|32/32|
|Case-level deletion-status accuracy|16/32 (50%)|32/32 (100.00%)|
|Exact rows|1/32|8/32 (25.00%)|
|Sequence accuracy|1/32|8/32 (25.00%)|
|Step precision|73/73|158/162 (97.53%)|
|Step recall|73/193|158/193 (81.87%)|
|Step F1|54.89%|89.01%|
|Field accuracy|481/1351|1060/1379 (76.87%)|
|Full prediction rows|Blocked|518, sorted and unique|

Final full command: `python -B code/main.py --run --with-extraction`, exit 0.
Distribution: 156 COMPLETE, 352 INCOMPLETE, 10 NOT_APPLICABLE. Model calls: 0.
CSV framing, allowed operation/state triples, citations/time metadata, numbering,
phase/operation/system/resource ordering and request coverage were checked.
Production publication retains uncertainty diagnostics but does not abstain.
An empty COMPLETE verification array is permitted only in the explicit prediction
path when no subject-linked resource is established; this is a prediction, not
proof of exhaustive deletion. Strict diagnostic APIs keep their original checks.
Hidden accuracy and exhaustive semantic correctness are NOT MEASURED.

## Participant-created evaluation cases

1. Retention witness and current readback in separate artifacts: current evidence
   and eligible interval combine; future, expired and other-copy controls defer.
2. Mixed obligations: an exposed search record plus an already compliant record
   retains the compliant verification; all INCOMPLETE future citations are empty.
3. Explicit catalog alias: opaque document reference joins only its exact catalog
   resource; future mappings, alias collisions and unrelated records do not join.
4. Quoted/negated order content: illustrative or negated prose is not treated as
   source-backed shared context in strict audit mode.

These are real fixtures in `code/tests/test_phase06b.py`; final measured suite:
538 passed in 23.06 seconds, no tests skipped. The one full-run CLI fixture was
updated for the expressly requested prediction publication behavior. Strict
policy, provenance, temporal and malformed-output fixture coverage remains.

## Failures and improvements

| Failure | Final change / remaining limit |
|---|---|
|Proof abstentions omit rows|Explicit prediction defaults publish every request; uncertainties retained in diagnostics|
|Undated security retention|User-authorized RETAIN prior; date is not claimed recovered|
|Attachment ownership unknown|Subject-linked attachment defaults to sole ownership unless other owners are explicit|
|Shared support context unknown|REDACT prior for linked support conversations|
|Restore permission without archive readback|Subject-linked restore entry defaults to affected backup; block/check restore|
|Contact lookup classified as analytics|Explicit email_opt_in contact schema selects SECONDARY_IDENTIFIER/DELETE|
|Compliant obligations omitted by incomplete-only output|Planner includes every established compliant verification alongside remediation|
|Unlinked absent/anonymized resources|Remain omitted; no numeric-ID fabrication. 24/32 public rows still differ from reference|

Selected new output exceeds fallback thresholds (fallback 25/32 statuses, 5/32
exact, 137/193 matching steps). Final 32/32 statuses does not imply perfect step
plans or hidden performance. Packaging checks reproducibility of these heuristic
predictions; independent proof diagnostics remain informative, not blocking.
