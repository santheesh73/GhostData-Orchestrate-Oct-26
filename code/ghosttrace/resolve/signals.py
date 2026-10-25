"""Explicit subject fields, not free-text token co-occurrence, establish links.

Query/lookup fields are target references rather than stored identifiers. SQL
wrappers are unwrapped; raw lines and record_json are never searched a second
time. Names, case IDs, numeric suffixes, and reported operation results do not
identify a person here.
"""

from ..ingest.normalization import normalize_identifier, strict_json

STRONG_KINDS = {"email", "email_hash", "phone"}
REFERENCE_KEYS = {"customer_reference", "subject_reference", "subject_ref", "stable_user_id",
                  "catalog_subject_reference", "subject_selector",
                  "user_id", "owner_user_id", "lookup_key", "match_key", "subject_key", "correlation_key",
                  "query", "lookup_value", "scan_key"}
LOOKUP_KEYS = {"query", "lookup_key", "match_key", "subject_key", "correlation_key", "scan_key"}
SKIP = {"raw_line", "record_json", "message", "header_fields", "message_fields", "details", "extraction_proof"}


def payload(observation):
    return strict_json(observation.payload_json)


def signals(value, known_users):
    """Return explicit stable references, typed aliases, and untyped lookups."""
    users, aliases, references = set(), set(), set()
    pending = [value]
    while pending:
        item = pending.pop()
        if not isinstance(item, dict):
            continue
        for key, val in item.items():
            if key in SKIP:
                continue
            if isinstance(val, dict):
                pending.append(val)
            elif isinstance(val, list):
                pending.extend(v for v in val if isinstance(v, dict))
                pending.extend({key: v} for v in val if isinstance(v, str))
            elif isinstance(val, str) and val.strip() and val.casefold() not in {"null", "none"}:
                if key in {"user_id", "stable_user_id", "owner_user_id"}:
                    users.add(val.strip())
                elif key in REFERENCE_KEYS:
                    if val.strip() in known_users:
                        users.add(val.strip())
                    else:
                        references.add(val.strip())
                elif key.endswith("email_hash"):
                    aliases.add(("email_hash", normalize_identifier("email_hash", val)))
                elif key.endswith("email"):
                    aliases.add(("email", normalize_identifier("email", val)))
                elif key.endswith("phone"):
                    aliases.add(("phone", normalize_identifier("phone", val)))
    return frozenset(users), frozenset(aliases), frozenset(references)


def eligible(observation, cutoff):
    available, observed = observation.evidence.available_at, observation.observed_at
    derived = observation.derived_available_at
    if (available is not None and available > cutoff) or (observed is not None and observed > cutoff) or (derived is not None and derived > cutoff):
        return "FUTURE"
    if available is None or observed is None:
        return "UNKNOWN_TIME"
    if observation.derived_valid_until is not None and cutoff >= observation.derived_valid_until:
        return "AMBIGUOUS_DERIVATION"
    return "ELIGIBLE"


def paired_aliases(value, known_users):
    """Ownership pairs must occupy the same object. An email in another
    message/document cannot become an alias of the only user ID in the envelope.
    Nested objects are inspected independently, never joined transitively.
    """
    result, pending = set(), [value]
    while pending:
        item = pending.pop()
        if not isinstance(item, dict):
            continue
        scalar = {key: val for key, val in item.items() if not isinstance(val, (dict, list))}
        users, aliases, _ = signals(scalar, known_users)
        if len(users) == 1:
            result.update((next(iter(users)), kind, alias) for kind, alias in aliases)
        for key, val in item.items():
            if key in SKIP:
                continue
            if isinstance(val, dict):
                pending.append(val)
            elif isinstance(val, list):
                pending.extend(v for v in val if isinstance(v, dict))
    return frozenset(result)


def aware(at):
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("reconstruction times must be timezone-aware")
