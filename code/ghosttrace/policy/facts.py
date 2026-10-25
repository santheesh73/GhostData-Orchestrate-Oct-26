"""Policy projections from direct observations, preserving per-field proofs."""

from ..ingest.normalization import canonical_json
from ..resolve.conflict_resolver import resolve_facts
from ..resolve.models import ResolvedFact, StateFact
from ..resolve.signals import payload
from ..resolve.temporal_replay import BOOL_FIELDS, READ_EVENTS, SCAN_EVENTS, extract_facts

DIRECT_FIELDS = {"name", "full_name", "display_name", "requester_name", "email", "customer_email",
                 "requester_email", "owner_email", "phone", "requester_phone", "email_hash",
                 "ip_address", "postal_address", "date_of_birth"}
REFERENCE_FIELDS = {"user_id", "stable_user_id", "customer_reference", "subject_reference", "subject_ref",
                    "owner_user_id", "subject_selector"}
TEXT_FIELDS = {"message_text", "message_excerpt", "body", "text", "notes"}
EXTRA_FIELDS = {"account_status", "shared_context", "sole_subject", "hold_active", "legal_hold_active",
                "retention_until", "retention_from", "restore_block_supported", "eligible", "deletion_block",
                "source_resource_id", "target_resource_id", "source_system", "target_system", "destination_system"}
BOOLEAN_FIELDS = BOOL_FIELDS | {"shared_context", "sole_subject", "hold_active", "legal_hold_active",
                               "restore_block_supported", "eligible", "deletion_block"}


def direct_key(key):
    return key in DIRECT_FIELDS or key.endswith(("email", "email_hash", "phone"))


def field_key(path):
    parts = path.split("/")
    return next((part for part in reversed(parts) if direct_key(part)), parts[-1])


def project(state):
    values, snapshots = [], []
    for observation in state.timeline:
        values.extend(extract_facts(observation))
        data = payload(observation)
        if observation.claim_kind == "SQL_RECORD" and isinstance(data.get("record"), dict):
            data = data["record"]
        if observation.claim_kind not in {"SQL_RECORD", "RECORD_SNAPSHOT"} and not (
            observation.claim_kind == "LOG_EVENT" and data.get("event") in READ_EVENTS | SCAN_EVENTS):
            continue
        if observation.claim_kind in {"SQL_RECORD", "RECORD_SNAPSHOT"}:
            snapshots.append((observation.observed_at, observation.observation_id))
        pending = [(data, "")]
        while pending:
            item, prefix = pending.pop()
            for key, value in sorted(item.items()):
                if key in {"raw_line", "record_json", "header_fields", "message_fields", "message", "extraction_proof"}:
                    continue
                path = prefix + "/" + key
                if isinstance(value, dict):
                    pending.append((value, path))
                elif isinstance(value, list):
                    if direct_key(key) or any(direct_key(part) for part in prefix.split("/")):
                        values.append(StateFact(state.resource, path, canonical_json(value),
                                                observation.observed_at, observation.observation_id))
                    pending.extend((child, path + "/" + str(i)) for i, child in enumerate(value) if isinstance(child, dict))
                elif key in REFERENCE_FIELDS | TEXT_FIELDS | EXTRA_FIELDS | BOOLEAN_FIELDS or direct_key(key) or any(direct_key(part) for part in prefix.split("/")):
                    if key in BOOLEAN_FIELDS:
                        if isinstance(value, str) and value.casefold() in {"true", "false"}:
                            value = value.casefold() == "true"
                        elif observation.claim_kind == "SQL_RECORD" and type(value) is int and value in {0, 1}:
                            value = bool(value)  # SQLite BOOLEAN/JSON scalar schema adapter only.
                        # Other representations remain raw/unknown. In
                        # particular a malformed scheduler must not disappear
                        # and make a disabled-flow proof look complete.
                    values.append(StateFact(state.resource, path, canonical_json(value),
                                            observation.observed_at, observation.observation_id))
    result = resolve_facts(values)
    boundaries = snapshots + [(f.observed_at, oid) for f in result if f.dimension == "presence"
                             and f.value_json == '"ABSENT"' for oid in f.observation_ids]
    if boundaries:
        latest = max(t for t, _ in boundaries)
        proof = tuple(sorted({oid for t, oid in boundaries if t == latest}))
        result = tuple(ResolvedFact(f.dimension, None, latest, proof) if f.dimension.startswith("/")
                       and f.observed_at < latest else f for f in result)
    return result


def named(facts, *names):
    return tuple(f for f in facts if f.dimension.rsplit("/", 1)[-1] in names)
