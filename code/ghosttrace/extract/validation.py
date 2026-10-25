"""Validate every cached/local/model extraction against its actual source."""

import math
import re

from ..ingest.normalization import strict_json
from ..models import Authorization
from ..policy.applicability import classify_request
from .local import MAX_PAGES, MAX_TEXT, MAX_UNITS
from .models import ExtractionError, TextUnit, Transcript

FIELD_NAMES = frozenset({"name", "full_name", "email", "phone", "email_hash", "user_id", "customer_reference",
    "subject_reference", "requester_email", "requester_name", "requester_phone", "owner_email", "record_type",
    "enabled", "scheduler_registered", "restore_allowed", "archive_present", "shared_context", "sole_subject",
    "hold_active", "retention_until", "account_status", "result", "message_text"})
BOOL_NAMES = frozenset({"enabled", "scheduler_registered", "restore_allowed", "archive_present", "shared_context",
                        "sole_subject", "hold_active"})
ANCHOR = re.compile(r"(?:resource\s*(?:id|reference)?|record\s*(?:id|reference)|event reference|account id|profile id|object key|support reference)\s*[:=#]?\s+([^\r\n]+)", re.IGNORECASE)


def validate_transcript(data):
    if not isinstance(data, dict) or set(data) != {"backend", "version", "pages", "units", "incomplete_pages"}:
        raise ExtractionError("INVALID_TRANSCRIPT")
    if type(data["pages"]) is not int or not 0 < data["pages"] <= MAX_PAGES:
        raise ExtractionError("INVALID_PAGE_COUNT")
    if not all(isinstance(data[k], str) and data[k] for k in ("backend", "version")):
        raise ExtractionError("INVALID_BACKEND_IDENTITY")
    if not isinstance(data["units"], (list, tuple)) or not 0 < len(data["units"]) <= MAX_UNITS:
        raise ExtractionError("INVALID_TEXT_UNITS")
    units, locators = [], set()
    for row in data["units"]:
        if not isinstance(row, dict) or set(row) != {"locator", "text", "page", "bbox"}:
            raise ExtractionError("INVALID_TEXT_UNIT")
        if (not isinstance(row["text"], str) or not row["text"].strip() or "\x00" in row["text"]
            or type(row["page"]) is not int or not 1 <= row["page"] <= data["pages"]
            or not isinstance(row["locator"], str) or not row["locator"].startswith(f"page:{row['page']}/")
            or row["locator"] in locators):
            raise ExtractionError("INVALID_TEXT_UNIT")
        box = row["bbox"]
        if not isinstance(box, (list, tuple)) or len(box) not in {0, 4} or any(
                type(v) not in {int, float} or not math.isfinite(v) or v < 0 for v in box):
            raise ExtractionError("INVALID_BOUNDING_BOX")
        units.append(TextUnit(row["locator"], row["text"], row["page"], tuple(box)))
        locators.add(row["locator"])
    if sum(len(u.text) for u in units) > MAX_TEXT:
        raise ExtractionError("DOCUMENT_TEXT_BUDGET_EXCEEDED")
    missing = data["incomplete_pages"]
    if not isinstance(missing, (list, tuple)) or any(type(n) is not int or not 1 <= n <= data["pages"] for n in missing):
        raise ExtractionError("INVALID_MISSING_PAGES")
    accounted = {u.page for u in units} | set(missing)
    if accounted != set(range(1, data["pages"] + 1)):
        raise ExtractionError("UNACCOUNTED_PAGE")
    return Transcript(data["backend"], data["version"], data["pages"], tuple(units), tuple(sorted(set(missing))))


def _quote(quote, locator, units):
    if not isinstance(quote, str) or not quote.strip() or locator not in units or quote not in units[locator]:
        raise ExtractionError("UNGROUNDED_QUOTE")


def validate_records(data, transcript, system, category):
    if not isinstance(data, dict) or set(data) != {"records", "uncertainties"}:
        raise ExtractionError("INVALID_RECORD_ENVELOPE")
    if (not isinstance(data["records"], list) or len(data["records"]) > 256
        or not isinstance(data["uncertainties"], list) or any(not isinstance(x, str) or len(x) > 200 for x in data["uncertainties"])):
        raise ExtractionError("INVALID_RECORD_ARRAY")
    units = {u.locator: u.text for u in transcript.units}
    for record in data["records"]:
        if not isinstance(record, dict) or set(record) != {"resource_id", "system_id", "category", "quote", "locator", "fields"}:
            raise ExtractionError("INVALID_RECORD")
        if record["system_id"] != system or not system or record["category"] != category:
            raise ExtractionError("UNSUPPORTED_SYSTEM_OR_CATEGORY")
        resource = record["resource_id"]
        if not isinstance(resource, str) or not resource.strip() or resource != resource.strip() or len(resource) > 256:
            raise ExtractionError("INVALID_RESOURCE_ANCHOR")
        _quote(record["quote"], record["locator"], units)
        match = ANCHOR.search(record["quote"])
        if not match or resource not in match[1].split():
            raise ExtractionError("INVALID_RESOURCE_ANCHOR")
        if not isinstance(record["fields"], list) or len(record["fields"]) > 64:
            raise ExtractionError("INVALID_FIELD_ARRAY")
        seen = set()
        for fact in record["fields"]:
            if not isinstance(fact, dict) or set(fact) != {"name", "value_json", "quote", "locator"}:
                raise ExtractionError("INVALID_FIELD")
            if fact["name"] not in FIELD_NAMES or fact["name"] in seen or not isinstance(fact["value_json"], str):
                raise ExtractionError("INVALID_FIELD_NAME")
            seen.add(fact["name"])
            _quote(fact["quote"], fact["locator"], units)
            label = fact["name"].replace("_", " ")
            if not re.match(r"[ _]".join(re.escape(part) for part in fact["name"].split("_")) + r"\s*[:=]?\s+", fact["quote"], re.IGNORECASE):
                raise ExtractionError("FIELD_LABEL_MISMATCH")
            value = strict_json(fact["value_json"])
            if fact["name"] in BOOL_NAMES:
                literal = re.search(r"[:=]\s*(true|false)\s*$", fact["quote"], re.IGNORECASE)
                if type(value) is not bool or not literal or value != (literal[1].casefold() == "true"):
                    raise ExtractionError("UNGROUNDED_BOOLEAN")
            elif value is None:
                if not re.search(r"[:=]\s*(null|none)\s*$", fact["quote"], re.IGNORECASE):
                    raise ExtractionError("UNGROUNDED_NULL")
            elif not isinstance(value, str) or not value or value not in fact["quote"]:
                raise ExtractionError("UNGROUNDED_VALUE")
    return data


def validate_intent(data, text):
    keys = {"authorization", "language", "english_translation", "quote"}
    if not isinstance(data, dict) or set(data) != keys or any(not isinstance(data[k], str) for k in keys):
        raise ExtractionError("INVALID_INTENT_RESULT")
    if data["authorization"] not in {a.value for a in Authorization} or any(len(v) > 16000 for v in data.values()):
        raise ExtractionError("INVALID_AUTHORIZATION")
    if not data["quote"].strip() or data["quote"] not in text:
        raise ExtractionError("UNGROUNDED_INTENT_QUOTE")
    authorization = Authorization(data["authorization"])
    translated = classify_request(data["english_translation"]).authorization
    if authorization != Authorization.UNRESOLVED and translated != authorization:
        raise ExtractionError("TRANSLATION_AUTHORIZATION_CONFLICT")
    return data
