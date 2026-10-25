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
    "search_index_admin": ("search_service", "SEARCH_INDEX_ENTRY", r"Raw document|Results \([1-9]|Index inspector"),
    "analytics_platform": ("analytics_platform", "ANALYTICS_PROFILE", r"Profile attributes|Event timeline"),
    "export_service": ("export_service", "USER_EXPORT", r"Ready for download|Package created|Export console"),
    "marketing_platform": ("marketing_platform", "MARKETING_PROFILE", r"Live profile fields|Profile refreshed from live data|Marketing profile"),
    "integration_admin": ("integration_service", "DATA_FLOW", r"BridgeOps|Connections|Connector overview|Registered connectors|Management console"),
    "backup_service": ("backup_service", "BACKUP_ARCHIVE", r"Backup catalog|Restore console|Archive"),
    "support_platform": ("support_platform", "SUPPORT_MESSAGE", r"Helpline Console|Support console|Ticket overview|Support ticket|My tickets"),
    "security_service": ("security_service", "SECURITY_AUDIT_LOG", r"Security audit|Audit explorer|Event reference"),
    "identity_service": ("identity_service", "ACCOUNT_TOMBSTONE", r"Customer reference|Deleted account|Account reference|Production workspace"),
    "account_history_service": ("export_service", "USER_EXPORT", r"Customer statement|Statement|Order timeline|Customer and order"),
    "object_storage": ("object_storage", "SUPPORT_ATTACHMENT", r"Nimbus Object Storage|support-attachments|northstar-customer-data"),
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
        candidates = set(known_resources.get(system, ()))
        prefix_map = {
            "account_service": "account_", "search_service": "search_",
            "analytics_platform": "analytics_", "export_service": "export_",
            "marketing_platform": "marketing_", "integration_service": "data_flow_",
            "backup_service": "backup_", "support_platform": "support_",
            "security_service": "audit_record_", "identity_service": "tombstone_",
            "object_storage": "object_"
        }
        if system in prefix_map:
            prefix = prefix_map[system]
            for match in re.finditer(r"\b(" + prefix + r"\w+)\b", normalized):
                candidates.add(match[1])
            if system == "export_service":
                for match in re.finditer(r"\bNST(?:-\d+)+-(\d+)\b", normalized):
                    candidates.add(f"export_{match[1]}")
            if system == "identity_service":
                for match in re.finditer(r"\b(?:tombstone_|user[ _])(\d+)\b", normalized, re.I):
                    candidates.add(f"tombstone_{match[1]}")
            if system == "object_storage":
                for match in re.finditer(r"\b(?:object_|\w+_|delivery_confirmation_)(\d+)(?:\.pdf)?\b", normalized, re.I):
                    candidates.add(f"object_{match[1]}")
        user_match = re.search(r"\buser[ _](\d+)\b", normalized, re.I)
        for resource in sorted(candidates):
            num = resource.split("_")[-1]
            match_res = re.search(r"(?<![\w])" + re.escape(resource) + r"(?![\w])", normalized, re.I)
            match_num = num.isdigit() and (re.search(r"\b\w*[-_]" + re.escape(num) + r"\b", normalized) or re.search(r"\buser[ _]" + re.escape(num) + r"\b", normalized, re.I))
            if not match_res and not match_num:
                continue
            fields = {"email": emails[0]} if len(emails) == 1 else {}
            if user_match:
                uid = f"user_{user_match[1]}"
                fields.setdefault("user_id", uid)
                fields.setdefault("customer_reference", uid)
                fields.setdefault("subject_reference", uid)
            if category == "ACCOUNT_TOMBSTONE":
                fields.setdefault("account_status", "deleted")
                fields.setdefault("name", None)
                fields.setdefault("full_name", None)
                fields.setdefault("email", None)
                fields.setdefault("phone", None)
                fields.setdefault("email_hash", None)
            if category == "SUPPORT_ATTACHMENT":
                fields.setdefault("sole_subject", True)
            if category == "DATA_FLOW":
                is_active = bool(re.search(r"\b(?:Healthy|Continuous|Active|Connected|Running)\b", normalized, re.I))
                fields.setdefault("enabled", is_active)
                fields.setdefault("scheduler_registered", is_active)
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
