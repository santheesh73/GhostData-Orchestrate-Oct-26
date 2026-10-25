"""Small, source-grounded business-schema adapters, with no verdicts or IDs.

These adapters recognize explicit form/panel structure. They never repair OCR
characters, infer missing identifiers, or derive negative state from empty text.
"""

from dataclasses import replace
from datetime import datetime, timezone
import re

from ..ingest.corpus import IngestionBundle
from ..ingest.evidence_index import EvidenceIndex
from ..ingest.normalization import make_observation
from ..resolve.signals import eligible, payload

PANELS = {
    "account_admin_portal": ("account_service", "USER_PROFILE", r"Customer details|Overview"),
    "search_index_admin": ("search_service", "SEARCH_INDEX_ENTRY", r"Raw document|Results \([1-9]"),
    "analytics_platform": ("analytics_platform", "ANALYTICS_PROFILE", r"Profile attributes|Event timeline"),
    "export_service": ("export_service", "USER_EXPORT", r"Ready for download|Package created"),
    "marketing_platform": ("marketing_platform", "MARKETING_PROFILE", r"Live profile fields|Profile refreshed from live data"),
}


def project_document(result, known_resources):
    text_observations = [o for o in result.observations if o.claim_kind == "DOCUMENT_TEXT"]
    if not text_observations or result.status.value != "PARSED":
        return ()
    text = "\n".join(payload(o)["text"] for o in text_observations)
    emails = sorted(set(re.findall(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w.-]+\.[A-Za-z]{2,}", text)))
    rows = []
    if "DELIVERY ADDRESS CORRECTION REQUEST" in text and re.search(r"\buploader customer\b", text, re.I):
        anchor = re.search(r"Support reference\s+[^/\n]+/\s*(\S+)", text)
        if anchor and len(emails) == 1:
            rows.append(("support_platform", "SUPPORT_ATTACHMENT", anchor[1],
                         {"email": emails[0], "sole_subject": True}, "SINGLE_CUSTOMER_UPLOAD_FORM"))
    if "SIGNED RECORD EXTRACT" in text:
        anchor = re.search(r"Event reference\s+(\S+)", text)
        subject = re.search(r"subject reference\s+(\S+)", text, re.I)
        until = re.search(r"retain until\s+(\d{1,2} [A-Za-z]{3} \d{4})\s+(\d{2})\s*[:\n ]\s*(\d{2})\s+UTC", text, re.I)
        if anchor and subject and until:
            try:
                clock = datetime.strptime(f"{until[1]} {until[2]}:{until[3]}", "%d %b %Y %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
            else:
                rows.append(("security_service", "SECURITY_AUDIT_LOG", anchor[1],
                             {"subject_reference": subject[1], "retention_until": clock.isoformat()}, "SIGNED_RETENTION_EXTRACT"))
    panel = PANELS.get(result.source.source_kind)
    if panel and re.search(panel[2], text, re.I) and not re.search(r"\b(?:0 hits|no records|not found)\b", text, re.I):
        system, category, _ = panel
        normalized = re.sub(r"\s*_\s*", "_", text)
        for resource in sorted(known_resources.get(system, ())):
            if not re.search(r"(?<![\w])" + re.escape(resource) + r"(?![\w])", normalized, re.I):
                continue
            fields = {"email": emails[0]} if len(emails) == 1 else {}
            # Only positive record presence is inferred from an actual record
            # panel; list/query text cannot prove absence or anonymization.
            rows.append((system, category, resource, fields, "POSITIVE_RESOURCE_PANEL"))
    observations = []
    for n, (system, category, resource, fields, rule) in enumerate(rows, 1):
        observations.append(make_observation(result.source, result.source_sha256, f"business-schema/{n}",
            {"resource_id": resource, "record_type": category, **fields,
             "extraction_proof": {"adapter": rule, "observation_ids": [o.observation_id for o in text_observations]}},
            system=system, resource=resource, category=category, physical_copy="document:" + result.source.evidence_id,
            observed_at=result.source.available_at, time_basis="document_capture"))
    return tuple(observations)


def enrich_business_documents(bundle):
    all_observations = bundle.index.all_observations()
    files = []
    for result in bundle.files:
        resources = {}
        for observation in all_observations:
            if (observation.resource.resource_id and result.source.available_at is not None
                    and eligible(observation, result.source.available_at) == "ELIGIBLE"):
                resources.setdefault(observation.resource.system_id, set()).add(observation.resource.resource_id)
        promoted = project_document(result, resources)
        if promoted:
            keys = {(o.resource.system_id, o.resource.resource_id) for o in promoted}
            original = tuple(o for o in result.observations if not (o.claim_kind == "RECORD_SNAPSHOT"
                and (o.resource.system_id, o.resource.resource_id) in keys))
            result = replace(result, observations=(*original, *promoted))
        files.append(result)
    index = EvidenceIndex(o for result in (*files, *bundle.context) for o in result.observations)
    return IngestionBundle(tuple(files), bundle.context, index, bundle.diagnostics)
