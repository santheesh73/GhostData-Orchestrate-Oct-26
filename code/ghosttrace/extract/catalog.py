"""Explicit catalog aliases bind literal business documents; never ID suffixes."""
from collections import defaultdict
import re

from ..ingest.normalization import make_observation
from ..resolve.signals import payload


def catalog_documents(result, observations):
    kinds = {"account_history_service": ("export_service", "USER_EXPORT", "catalog_label"),
             "object_storage": ("object_storage", "SUPPORT_ATTACHMENT", "catalog_filename")}
    schema = kinds.get(result.source.source_kind)
    if schema is None or result.source.available_at is None or result.status.value != "PARSED":
        return ()
    system, category, field = schema
    units = [(o, line.strip()) for o in result.observations if o.claim_kind == "DOCUMENT_TEXT"
             for line in payload(o)["text"].splitlines() if line.strip()]
    matches = defaultdict(list)
    for o in observations:
        d = payload(o)
        if (o.claim_kind != "OPERATION_CLAIM" or o.evidence.path != "system_activity.csv"
                or d.get("event_type") != "LINK_RESOURCE_IDENTITY" or o.resource.system_id != system
                or o.evidence.available_at is None or o.observed_at is None):
            continue
        label = d.get(field)
        if not isinstance(label, str) or not label.strip():
            continue
        grammar = (r"Data catalog linked (\S+) \(([^()]*)\) to (\S+) and (\S+)\." if field == "catalog_label" else
                   r"Attachment catalog confirmed (\S+) \(([^()]*)\) belongs only to (\S+) and (\S+); no other subject is linked\.")
        match = re.fullmatch(grammar, d.get("details", ""))
        if not match or match[1] != o.resource.resource_id or match[2] != label:
            continue
        # Entire line equality prevents suffix matching and incidental substrings.
        literal = [(unit, line) for unit, line in units if line == label or
                   (field == "catalog_label" and line.casefold() == ("Statement " + label).casefold())]
        if literal:
            matches[label].append((o, d, literal))
    result_rows = []
    for label, bindings in sorted(matches.items()):
        o, d, literal = min(bindings, key=lambda b: (max(b[0].observed_at, b[0].evidence.available_at), b[0].observation_id))
        not_before = max(result.source.available_at, o.observed_at, o.evidence.available_at)
        resource = o.resource.resource_id
        conflicts = [max(c.observed_at, c.evidence.available_at) for c, _, _ in bindings if c.resource.resource_id != resource]
        until = min(conflicts) if conflicts else None
        if until is not None and until <= not_before:
            continue
        result_rows.append(make_observation(result.source, result.source_sha256,
            "business-schema/catalog:" + str(len(result_rows) + 1),
            {"resource_id": resource, "record_type": category, "extraction_proof": {
                "adapter": "EXPLICIT_CATALOG_ALIAS", "catalog_observation_id": o.observation_id,
                "catalog_evidence_id": o.evidence.evidence_id, "catalog_locator": o.location,
                "catalog_quote": d["details"], "alias": label,
                "document_spans": [{"locator": unit.location, "text": line} for unit, line in literal]}},
            system=system, resource=resource, category=category,
            physical_copy="document:" + result.source.evidence_id,
            observed_at=result.source.available_at, time_basis="document_capture",
            derived_available_at=not_before, derived_valid_until=until))
    return tuple(result_rows)
