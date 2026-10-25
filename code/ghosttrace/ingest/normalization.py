"""Lossless observation normalization; no identity merging or privacy verdicts.

Facts contain canonical JSON values (so null/false/empty remain distinct).
The payload and source hash retain the extraction boundary. Candidate identifiers
are retrieval keys only, never proof of subject ownership.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
import re

from ..models import EvidenceSource, Identifier, Observation, Resource
from .loader import InputError, parse_timestamp

# JUDGEMENT bounds: parsing safety, not dataset-fitted classification thresholds.
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_DEPTH = 64
MAX_UNITS = 100_000
# Bounded candidate token matching avoids quadratic scans of long unbroken text.
_EMAIL = re.compile(r"(?<![A-Za-z0-9.!#$%&'*+/=?^_`{|}~@-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,256}@[A-Za-z0-9.-]{1,255}\.[A-Za-z]{2,63}(?![A-Za-z0-9.@-])")


class ParseStatus(str, Enum):
    PARSED = "PARSED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    DEFERRED = "DEFERRED"
    EMPTY = "EMPTY"


@dataclass(frozen=True, slots=True)
class ParseDiagnostic:
    code: str
    location: str
    detail: str
    severity: str = "WARNING"


@dataclass(frozen=True, slots=True)
class ParseResult:
    source: EvidenceSource
    format: str
    status: ParseStatus
    source_sha256: str
    observations: tuple[Observation, ...] = ()
    diagnostics: tuple[ParseDiagnostic, ...] = ()
    units_seen: int = 0
    units_parsed: int = 0


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def strict_json(text: str):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def invalid(_):
        raise ValueError("non-finite JSON number")
    value = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > MAX_DEPTH:
            raise ValueError("JSON nesting exceeds supported depth")
        if isinstance(item, dict):
            pending.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            pending.extend((v, depth + 1) for v in item)
    return value


def normalize_identifier(kind: str, value: str) -> str:
    value = value.strip()
    if kind in {"email", "email_hash"}:
        return value.casefold()
    if kind == "phone" and value.startswith("+"):
        return "+" + "".join(c for c in value if c.isdecimal())
    return value


def identifiers_from(payload: dict, evidence_id: str) -> tuple[Identifier, ...]:
    found = set()
    def add(kind, value):
        if isinstance(value, str) and value.strip() and value.strip().casefold() not in {"null", "none", "no direct identifier"}:
            found.add((kind, value))
    pending = [payload]
    while pending:
        item = pending.pop()
        if isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    pending.append(value)
                    continue
                name = key.casefold()
                if name.endswith("email_hash"):
                    add("email_hash", value)
                elif name.endswith("email"):
                    add("email", value)
                elif name.endswith("phone"):
                    add("phone", value)
                elif name in {"name", "full_name", "display_name", "requester_name"}:
                    add("name", value)
                elif name in {"user_id", "stable_user_id", "owner_user_id"}:
                    add("user_id", value)
                elif name in {"resource_id", "source_resource_id"}:
                    add("resource_id", value)
                elif name in {"customer_reference", "subject_reference", "subject_ref", "lookup_key", "match_key", "subject_key", "correlation_key", "query"}:
                    add("reference", value)
                if isinstance(value, str):
                    for email in _EMAIL.findall(value):
                        add("email", email.rstrip(".,;"))
                    for user in re.findall(r"\buser_[A-Za-z0-9_-]+\b", value):
                        add("user_id", user)
            if item.get("field_name") in {"email", "email_hash", "phone"}:
                for key in ("old_value", "new_value"):
                    add(item["field_name"], item.get(key))
    return tuple(Identifier(kind, value, evidence_ids=(evidence_id,)) for kind, value in sorted(found))


def make_observation(source: EvidenceSource, digest: str, location: str, payload: dict,
                     *, system: str = "", resource: str = "", category: str = "",
                     physical_copy: str = "", observed_at: datetime | None = None,
                     time_basis: str = "unknown", claim_kind: str = "RECORD_SNAPSHOT",
                     trace_id: str = "", derived_available_at: datetime | None = None,
                     derived_valid_until: datetime | None = None) -> Observation:
    encoded = canonical_json(payload)
    identity = canonical_json([source.evidence_id, digest, location, physical_copy, encoded,
                               source.available_at.isoformat() if source.available_at else None,
                               source.source_kind, source.path, source.citeable])
    if derived_available_at is not None:
        identity += canonical_json(["derived_available_at", derived_available_at.isoformat()])
    if derived_valid_until is not None:
        identity += canonical_json(["derived_valid_until", derived_valid_until.isoformat()])
    facts = tuple((key, canonical_json(value)) for key, value in sorted(payload.items()))
    return Observation(Resource(system, resource, category, physical_copy), source, observed_at,
                       claim_kind, facts, location, hashlib.sha256(identity.encode("utf-8")).hexdigest(),
                       digest, encoded, identifiers_from(payload, source.evidence_id), time_basis, trace_id, derived_available_at, derived_valid_until)


def observation_time(payload: dict, inherited: datetime | None, inherited_basis: str,
                     diagnostics: list, location: str):
    # Record observation/event times precede enclosing capture time. created_at,
    # expires_at, and updated_at remain facts; they are not observation clocks.
    for key in ("observed_at", "recorded_at", "event_time", "captured_at"):
        if key in payload:
            try:
                return parse_timestamp(payload[key], key), key
            except InputError:
                diagnostics.append(ParseDiagnostic("INVALID_TIMESTAMP", location,
                                                   f"invalid {key}; observation time remains unknown", "ERROR"))
                return None, "unknown"
    return inherited, inherited_basis


def finish(source, format_name, digest, observations, diagnostics, seen, parsed):
    if seen == 0 and not diagnostics:
        status = ParseStatus.EMPTY
    elif diagnostics:
        status = ParseStatus.PARTIAL if observations else ParseStatus.FAILED
    else:
        status = ParseStatus.PARSED
    return ParseResult(source, format_name, status, digest, tuple(observations), tuple(diagnostics), seen, parsed)
