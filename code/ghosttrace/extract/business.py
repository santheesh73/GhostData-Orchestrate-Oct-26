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


def _ui_records(lines, text, origin, known_subjects):
    """Read explicit panel/column bindings without a pre-existing ID catalog.

    Identifier syntax locates visible text only; it never determines a policy
    category or verdict. Category comes from the declared business component.
    Ambiguous or unequal columns remain uninterpreted.
    """
    rows = []
    email_pattern = r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w.-]+\.[A-Za-z]{2,}"
    if origin == "export_service":
        ids_at = next((i for i, line in enumerate(lines) if re.sub(r"\W", "", line).casefold() == "exportid"), None)
        filename_at = next((i for i, line in enumerate(lines) if line.casefold() == "filename"), None)
        owners_at = next((i for i, line in enumerate(lines) if line.casefold() == "owner"), None)
        if ids_at is not None and filename_at is not None and owners_at is not None and ids_at < filename_at < owners_at:
            ids = [line for line in lines[ids_at + 1:filename_at] if re.fullmatch(r"[^\s]+_[^\s]*\d[^\s]*", line)]
            # The next column/header terminates the owner column. Never align a
            # truncated list by a guessed offset or use a footer's repeated row.
            owners = []
            started = False
            for line in lines[owners_at + 1:]:
                if re.fullmatch(email_pattern, line):
                    owners.append(line)
                    started = True
                elif started:
                    break
            if ids and len(ids) == len(owners) and len(ids) == len(set(ids)):
                rows.extend(("export_service", "USER_EXPORT", resource, {"owner_email": email}, "EXPORT_TABLE_COLUMNS")
                            for resource, email in zip(ids, owners))
    for line in lines:
        tokens = line.split()
        if origin == "analytics_platform" and len(tokens) == 3 and tokens[0] in known_subjects and re.fullmatch(email_pattern, tokens[2]):
            rows.append(("analytics_platform", "ANALYTICS_PROFILE", tokens[1],
                         {"customer_reference": tokens[0], "email": tokens[2]}, "ANALYTICS_SUBJECT_HEADER"))
        if origin == "marketing_platform" and len(tokens) >= 2 and re.fullmatch(email_pattern, tokens[1]) and tokens[0].casefold() not in {"email", "owner", "contact", "customer", "sender"} and "Live profile fields updated" in text:
            rows.append(("marketing_platform", "MARKETING_PROFILE", tokens[0], {"email": tokens[1]}, "MARKETING_PROFILE_HEADER"))
    if origin == "search_index_admin":
        anchors = [m[1] for line in lines if (m := re.fullmatch(r"Raw document\s*[•:-]\s*(\S+)", line, re.I))]
        subjects = re.findall(r"\bcustomer_reference[ \t]+(\S+)", text)
        if len(set(anchors)) == len(set(subjects)) == 1 and subjects[0] in known_subjects:
            rows.append(("search_service", "SEARCH_INDEX_ENTRY", anchors[0],
                         {"customer_reference": subjects[0]}, "SELECTED_SEARCH_DOCUMENT"))
    # Some panels display one opaque resource token without an ID label. Only a
    # unique visible candidate qualifies; no OCR character correction is used.
    candidates = {token for line in lines for token in re.findall(r"(?<![\w])([\w-]+_[\w-]*\d[\w-]*)(?![\w])", line)
                  if token not in known_subjects}
    if len(candidates) == 1 and origin == "integration_admin":
        selectors = [i for i, line in enumerate(lines) if line.casefold() == "selector"]
        if selectors:
            tail = "\n".join(lines[selectors[-1] + 1:])
            emails = set(re.findall(email_pattern, tail))
            if len(emails) == 1 and re.search(r"Continuous\s*S\s*y\s*n\s*c\b", tail, re.I) and re.search(r"\b[1-9]\d* events delivered\b", tail, re.I):
                rows.append(("integration_service", "DATA_FLOW", next(iter(candidates)),
                             {"subject_selector": next(iter(emails)), "enabled": True}, "LIVE_CONNECTOR_DELIVERIES"))
    if len(candidates) == 1 and origin == "support_platform" and all(label in text for label in ("Conversation", "Sender", "Assigned agent")):
        emails = set(re.findall(email_pattern, text))
        if len(emails) == 1:
            fields = {"requester_email": next(iter(emails))}
            references = {m[1] for line in lines if (m := re.fullmatch(r"order\s+(\S+)", line, re.I))
                          and m[1].casefold() not in {"status", "update", "details", "unknown", "none", "null"}}
            if len(references) == 1:
                fields["order_reference"] = next(iter(references))
            rows.append(("support_platform", "SUPPORT_MESSAGE", next(iter(candidates)),
                         fields, "CUSTOMER_AGENT_CONVERSATION_PANEL"))
    return rows


def project_document(result, known_resources, known_subjects=()):
    text_observations = [o for o in result.observations if o.claim_kind == "DOCUMENT_TEXT"]
    if not text_observations or result.status.value != "PARSED":
        return ()
    text = "\n".join(payload(o)["text"] for o in text_observations)
    lines = [re.sub(r"\s*_\s*", "_", line.strip()) for line in text.splitlines() if line.strip()]
    emails = sorted(set(re.findall(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w.-]+\.[A-Za-z]{2,}", text)))
    rows = []
    # Explicit labeled records go through the same field/quote validation as
    # local extraction. Omitted fields are not inserted as null or false.
    panel = PANELS.get(result.source.source_kind)
    labeled_proofs = {}
    if panel:
        from .documents import local_records
        from .models import TextUnit, Transcript
        units = tuple(TextUnit(o.location, payload(o)["text"], payload(o).get("page", 1), ()) for o in text_observations)
        transcript = Transcript("business-labeled", "1", max(u.page for u in units), units, ())
        for record in local_records(transcript, panel[0], panel[1])["records"]:
            from ..ingest.normalization import strict_json
            fields = {f["name"]: strict_json(f["value_json"]) for f in record["fields"]}
            if fields.get("record_type", panel[1]) == panel[1] and (not re.search(r"\b(?:0 hits|no records|not found)\b", text, re.I) or fields.get("result") in {"NOT_FOUND", "MISS"}):
                rows.append((panel[0], panel[1], record["resource_id"], fields, "EXPLICIT_LABELED_RECORD"))
                labeled_proofs[(panel[0], record["resource_id"])] = record
    if "DELIVERY ADDRESS CORRECTION REQUEST" in text and re.search(r"\buploader customer\b", text, re.I):
        # A support ticket reference is not an attachment identifier.
        anchor = re.search(r"Attachment ID\s*[:=]\s*(\S+)", text, re.I)
        rule = "EXPLICIT_ATTACHMENT_FORM"
        if anchor is None and re.search(r"Continued\s*[-–]\s*Attachment properties and upload history", text, re.I) and re.search(r"\bfile\s+\S+\.pdf\b", text, re.I):
            # The continued attachment-properties section binds the form's
            # literal internal support reference to this attachment. Neither
            # the customer uploader nor the single contact proves exclusivity.
            reference = re.search(r"Support reference\s+\S+\s*/\s*(\S+)", text, re.I)
            anchor = reference
            rule = "ATTACHMENT_PROPERTIES_REFERENCE"
        if anchor and len(emails) == 1:
            rows.append(("support_platform", "SUPPORT_ATTACHMENT", anchor[1],
                         {"email": emails[0]}, rule))
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
        hits = [r for r in known_resources.get(system, ()) if re.search(r"(?<![\w])" + re.escape(r) + r"(?![\w])", normalized, re.I)]
        for resource in sorted(hits if len(hits) == 1 else ()):
            if not re.search(r"(?<![\w])" + re.escape(resource) + r"(?![\w])", normalized, re.I):
                continue
            fields = {"email": emails[0]} if len(emails) == 1 else {}
            # Only positive record presence is inferred from an actual record
            # panel; list/query text cannot prove absence or anonymization.
            rows.append((system, category, resource, fields, "POSITIVE_RESOURCE_PANEL"))
    if not re.search(r"\b(?:0 hits|no records|not found)\b", text, re.I):
        rows.extend(_ui_records(lines, text, result.source.source_kind, known_subjects))
    # Combine compatible views of one displayed row without duplicating its
    # public resource or silently overwriting contradictory extracted values.
    combined = {}
    for system, category, resource, fields, rule in rows:
        key = system, category, resource
        old = combined.get(key)
        if old is None:
            combined[key] = (dict(fields), {rule})
        elif all(k not in old[0] or old[0][k] == value for k, value in fields.items()):
            old[0].update(fields)
            old[1].add(rule)
        else:
            # Conflicting source layouts cannot yield an authoritative row.
            combined[key] = ({}, {"AMBIGUOUS_PANEL_FIELDS"})
    rows = [(s, c, r, fields, "+".join(sorted(rules))) for (s, c, r), (fields, rules) in combined.items()
            if "AMBIGUOUS_PANEL_FIELDS" not in rules]
    observations = []
    for n, (system, category, resource, fields, rule) in enumerate(rows, 1):
        observations.append(make_observation(result.source, result.source_sha256, f"business-schema/{n}",
            {"resource_id": resource, "record_type": category, **fields,
             "extraction_proof": {"adapter": rule, "observation_ids": [o.observation_id for o in text_observations],
                                  "labeled_record": labeled_proofs.get((system, resource))}},
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
        subjects = {payload(o).get("user_id") for o in all_observations if o.claim_kind == "IDENTITY_REGISTRY_ENTRY"
                    and o.evidence.path == "user_identities.csv" and not o.evidence.citeable
                    and o.observed_at is not None and result.source.available_at is not None and o.observed_at <= result.source.available_at}
        from .catalog import catalog_documents
        promoted = (*project_document(result, resources, subjects), *catalog_documents(result, all_observations))
        if promoted:
            keys = {(o.resource.system_id, o.resource.resource_id) for o in promoted}
            original = tuple(o for o in result.observations if not (o.claim_kind == "RECORD_SNAPSHOT"
                and (o.resource.system_id, o.resource.resource_id) in keys))
            result = replace(result, observations=(*original, *promoted))
        files.append(result)
    index = EvidenceIndex(o for result in (*files, *bundle.context) for o in result.observations)
    return IngestionBundle(tuple(files), bundle.context, index, bundle.diagnostics)
