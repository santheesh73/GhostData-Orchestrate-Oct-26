"""Ground literal record fields; preserve all other text as candidate evidence."""

import re

from ..ingest.normalization import canonical_json, strict_json
from .validation import ANCHOR, BOOL_NAMES, FIELD_NAMES, validate_records

SYSTEMS = {"account_admin_portal": "account_service", "search_index_admin": "search_service",
           "integration_admin": "integration_service", "analytics_platform": "analytics_platform",
           "export_service": "export_service", "support_platform": "support_platform",
           "backup_service": "backup_service", "security_service": "security_service",
           "identity_service": "identity_service", "object_storage": "object_store",
           "account_history_service": "account_service", "legal_retention_service": "legal_service"}
# Only unambiguous source schema categories. Ambiguous ordinary documents do
# not become USER_PROFILE/SUPPORT_ATTACHMENT merely because they mention a user.
CATEGORIES = {"security_service": "SECURITY_AUDIT_LOG"}
LABELS = {name.replace("_", " "): name for name in FIELD_NAMES}
LABELS.update({"subject reference": "subject_reference", "retain until": "retention_until"})


def local_records(transcript, system, category):
    records, current = [], None
    for unit in transcript.units:
        for raw in unit.text.splitlines():
            line = raw.strip()
            anchor = ANCHOR.match(line)
            if anchor:
                # A reference can contain multiple opaque IDs, e.g. support
                # ticket / attachment. Ambiguity is preserved rather than guessed.
                tokens = anchor[1].split()
                if len(tokens) == 1:
                    current = {"resource_id": tokens[0], "system_id": system, "category": category,
                               "quote": line, "locator": unit.locator, "fields": []}
                    records.append(current)
                else:
                    current = None
                continue
            if current is None:
                continue
            for label, name in sorted(LABELS.items(), key=lambda p: -len(p[0])):
                match = re.fullmatch(re.escape(label) + r"\s*[:=]\s*(.+)", line, re.IGNORECASE)
                if name == "subject_reference" and match is None:
                    match = re.fullmatch(r"subject reference\s+(\S+)", line, re.IGNORECASE)
                if not match or name in {f["name"] for f in current["fields"]}:
                    continue
                literal = match[1]
                if name in BOOL_NAMES:
                    if literal.casefold() not in {"true", "false"}:
                        continue
                    value = literal.casefold() == "true"
                else:
                    value = None if literal.casefold() in {"null", "none"} else literal
                current["fields"].append({"name": name, "value_json": canonical_json(value),
                                           "quote": line, "locator": unit.locator})
                break
    result = {"records": records, "uncertainties": []}
    return validate_records(result, transcript, system, category) if system else {"records": [], "uncertainties": ["UNKNOWN_DOCUMENT_SYSTEM"]}
