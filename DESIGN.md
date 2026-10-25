# GHOSTTRACE implemented design

This documents the existing compiler; it introduces no second architecture.

Input: participant-facing dataset only. Runtime never imports public sample
answers, generator internals or organizer labels. Output columns, statuses,
15 operations, seven step fields and order are transcribed in spec_registry
and independently in quality/validator.py from the official specification.

The stages are ingestion/index -> historical identity/temporal replay ->
policy obligations -> ordered canonical emission -> independent validation.
Canonical models are frozen dataclasses. Ownership is tied to subject identifiers,
not case or resource suffixes. Each resource has separate physical-copy state.
Observations carry source IDs, hashes, locators and observation/availability clocks.
Both clocks must be at/before audit_at. Canonical identity updated_at is a
non-citeable validity anchor; it is never a record-state citation.

Recovery keeps native OCR and catalog grammar fixes. Document adapters emit only
literal/explicitly bound IDs and supported fields; omitted values remain absent.
Labeled records retain field quotations and source locators. Business panel
projections carry their adapter and source text observation IDs. Ambiguous layouts
or conflicting values remain unresolved. A support ticket is not automatically
an attachment. An uploader/email is not exclusive ownership.

Policy conditions are TRUE/FALSE/UNKNOWN. Missing retention bounds, hold state,
shared context or exclusive ownership cannot authorize treatment or prove
compliance. Explicit agent/order context can establish a shared-context condition.
Restore permission and archive existence are separate facts. Proposed precaution
is not an observed active risk. Required retained records are never deleted by a
fallback. Tombstones require deleted status, a stable reference and PII treatment.
Uninterpreted message excerpts/bodies/notes cannot establish negative PII recall.
A small complete generic-summary language is separately interpreted and tested;
unknown words, names, digits and extra sentences remain unresolved.

Finite-corpus coverage checks source accounting, eligible linked states and
uninterpreted matching documents. This does not assert coverage beyond supplied
data. Unknown cases stay internal; no fallback official label is invented.
The writer publishes root output.csv atomically only after all518 official cases
and proof/CSV gates pass; otherwise it preserves prior output and exits3.

Optional AI returns source-quoted typed extraction only. It cannot choose policy
or invent labels/IDs. Calls default tozero and require explicit opt-in; no paid
calls occurred in recovery. Cache entries are source/backend/config bound and
revalidated. Local PDF/Windows OCR are measured; other-platform OCR and live
provider quality remain unverified. No model can recover absent source facts.

Packaging uses an explicit release-files inventory, independent full-contract
validation, a fresh source-grounded audit comparison, member hashes, secret-pattern
checks and a new staged destination. Shape-only diagnostics cannot build a bundle.
No existing submission is overwritten. A blocked semantic gate blocks packaging.
