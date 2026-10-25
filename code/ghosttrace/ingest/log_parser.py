"""Preserve every nonblank log event; trace linkage is retrieval, not identity.

Adapters handle key/value, JSON payload, bracket, pipe, syslog, and escaped cloud
envelopes. Unknown lines remain explicitly unparsed instead of being discarded.
"""

import re

from .loader import InputError, parse_timestamp
from .normalization import MAX_UNITS, ParseDiagnostic, finish, make_observation, strict_json

_KV = re.compile(r'(?<![A-Za-z0-9_.-])([A-Za-z_][A-Za-z0-9_.-]{0,127})=("(?:\\.|[^"\\])*"|[^\s]+)')
_PREFIX = re.compile(r'^(\d{4}-\d\d-\d\dT\S+)\s+(.*)$')
# The manifest names the logical owning service; replica process names remain
# in the payload and physical instance, rather than becoming public systems.
SERVICE_ALIASES = {"support_replica": "support_platform"}


def _atoms(text, diagnostics, location):
    values = {}
    for match in _KV.finditer(text):
        key, value = match.groups()
        if key in values:
            diagnostics.append(ParseDiagnostic("DUPLICATE_LOG_KEY", location, "repeated key retained in raw line"))
        try:
            values[key] = strict_json(value)
        except (ValueError, RecursionError):
            values[key] = value
            if value.startswith('"'):
                diagnostics.append(ParseDiagnostic("INVALID_LOG_VALUE", location, "invalid quoted log value retained raw", "ERROR"))
    return values


def parse_log(text, source, digest):
    observations, diagnostics = [], []
    seen = parsed = 0
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        seen += 1
        if seen > MAX_UNITS:
            raise ValueError("log event budget exceeded")
        location = f"line:{number}"
        match = _PREFIX.match(raw)
        fields = {}
        clock, basis = None, "unknown"
        if match:
            timestamp, body = match.groups()
            try:
                clock, basis = parse_timestamp(timestamp, "log event_time"), "event_time"
            except InputError:
                diagnostics.append(ParseDiagnostic("INVALID_TIMESTAMP", location, "invalid log event timestamp", "ERROR"))
            try:
                if body.startswith("{"):
                    fields = strict_json(body)
                    if not isinstance(fields, dict):
                        raise ValueError("event payload must be an object")
                else:
                    fields = _atoms(body, diagnostics, location)
                    bracket = re.match(r'^\[([^]]+)\]\s+\[([^]]+)\]\s+\[([^]]+)\]\s+(\w+):', body)
                    pipe = re.match(r'^\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|', body)
                    syslog = re.match(r'^<\d+>1\s+\S+\s+(\S+)\s+(\S+)\s+-\s+-\s+', body)
                    header_fields = {}
                    if bracket:
                        level, service, trace, event = bracket.groups()
                        header_fields = dict(level=level, service=service, trace_id=trace, event=event)
                    elif pipe:
                        level, service, trace, event = (v.strip() for v in pipe.groups())
                        header_fields = dict(level=level, service=service, trace_id=trace, event=event)
                    elif syslog:
                        header_fields = dict(service=syslog[1], trace_id=syslog[2])
                    if header_fields:
                        fields["header_fields"] = header_fields
                        for key, value in header_fields.items():
                            if key in fields and fields[key] != value:
                                diagnostics.append(ParseDiagnostic("ENVELOPE_CONFLICT", location, "header/payload field values conflict"))
                            fields.setdefault(key, value)
                    if isinstance(fields.get("message"), str):
                        inner = _atoms(fields["message"], diagnostics, location)
                        fields["message_fields"] = inner
                        for key, value in inner.items():
                            if key in fields and fields[key] != value:
                                diagnostics.append(ParseDiagnostic("ENVELOPE_CONFLICT", location, "inner/outer field values conflict"))
                            else:
                                fields[key] = value
                        fields.setdefault("service", fields.get("function", ""))
                        fields.setdefault("trace_id", fields.get("requestId", ""))
            except (ValueError, RecursionError):
                diagnostics.append(ParseDiagnostic("INVALID_LOG_PAYLOAD", location, "malformed structured log payload", "ERROR"))
                fields = {}
        recognized = isinstance(fields.get("event"), str) and bool(fields["event"].strip())
        if not recognized:
            diagnostics.append(ParseDiagnostic("UNPARSED_LOG_LINE", location, "line retained without a recognized event envelope"))
        else:
            parsed += 1
        # Raw line preserves duplicates, quoting, and any non-KV text for review.
        fields["raw_line"] = raw
        system = fields.get("system", fields.get("origin_system", fields.get("service", "")))
        if "system" not in fields and "origin_system" not in fields and SERVICE_ALIASES.get(system) == source.source_kind:
            system = source.source_kind
        resource = fields.get("resource_id", "")
        trace = fields.get("trace_id", "")
        observations.append(make_observation(source, digest, location, fields,
            system=str(system), resource=str(resource) if resource is not None else "",
            category=str(fields.get("record_type", "")), physical_copy=str(fields.get("instance", "")),
            observed_at=clock, time_basis=basis, claim_kind="LOG_EVENT" if recognized else "RAW_UNPARSED",
            trace_id=str(trace) if trace is not None else ""))
    # Transfer only causal query metadata, inside this file/service/instance and
    # trace. Resolve by timestamps, not physical line order, and reject tied
    # conflicting starts rather than selecting an arbitrary backend.
    starts = {}
    for observation in observations:
        data = strict_json(observation.payload_json)
        if observation.trace_id and observation.observed_at is not None and str(data.get("event", "")).endswith("_started") and isinstance(data.get("source"), str):
            key = (observation.resource.system_id, observation.resource.physical_copy, observation.trace_id, data["event"].removesuffix("_started"))
            starts.setdefault(key, []).append((observation.observed_at, data["source"], observation.location))
    normalized = []
    for observation in observations:
        data = strict_json(observation.payload_json)
        key = (observation.resource.system_id, observation.resource.physical_copy, observation.trace_id, str(data.get("event", "")).removesuffix("_completed"))
        eligible_starts = [s for s in starts.get(key, ()) if observation.observed_at is not None and s[0] <= observation.observed_at]
        if observation.trace_id and str(data.get("event", "")).endswith("_completed") and eligible_starts:
            clock = max(s[0] for s in eligible_starts)
            latest = [s for s in eligible_starts if s[0] == clock]
            backends = {s[1] for s in latest}
            if len(backends) == 1:
                backend = next(iter(backends))
                if "lookup_source" not in data or data["lookup_source"] == backend:
                    data["lookup_source"] = backend
                    data["lookup_source_locator"] = sorted(s[2] for s in latest)
                    observation = make_observation(source, digest, observation.location, data,
                        system=observation.resource.system_id, resource=observation.resource.resource_id,
                        category=observation.resource.category, physical_copy=observation.resource.physical_copy,
                        observed_at=observation.observed_at, time_basis=observation.time_basis,
                        claim_kind=observation.claim_kind, trace_id=observation.trace_id)
        normalized.append(observation)
    return finish(source, "log", digest, normalized, diagnostics, seen, parsed)


def parse_text(text, source, digest):
    """Pipe-delimited handover records; preserve other narrative as unparsed."""
    observations, diagnostics = [], []
    seen = parsed = 0
    clock = None
    for number, raw in enumerate(text.splitlines(), 1):
        stripped, location = raw.strip(), f"line:{number}"
        if not stripped:
            continue
        if stripped.startswith("Snapshot:"):
            try:
                clock = parse_timestamp(stripped.partition(":")[2].strip(), "text snapshot")
            except InputError:
                diagnostics.append(ParseDiagnostic("INVALID_TIMESTAMP", location, "invalid text snapshot timestamp", "ERROR"))
            continue
        if stripped.startswith("- ") and " | " in stripped:
            seen += 1
            parts = stripped[2:].split(" | ")
            if len(parts) == 6:
                timestamp, system, resource, category, result, reference = parts
                try:
                    observed = parse_timestamp(timestamp, "handover record")
                except InputError:
                    diagnostics.append(ParseDiagnostic("INVALID_TIMESTAMP", location, "invalid handover timestamp", "ERROR"))
                    observed = None
                payload = dict(recorded_at=timestamp, system=system, resource_id=resource,
                               record_type=category, result=result, subject_reference=reference,
                               raw_line=raw)
                if category == "DATA_FLOW" and result in {"ACTIVE", "DISABLED"}:
                    payload["enabled"] = result == "ACTIVE"
                if category == "BACKUP_ARCHIVE" and result in {"ACTIVE", "BLOCKED"}:
                    payload.update(restore_allowed=result == "ACTIVE", archive_present=True)
                if result in {"IDENTIFIABLE", "REDACTED", "ANONYMIZED"}:
                    payload["identifier_treatment"] = result
                observations.append(make_observation(source, digest, location, payload,
                    system=system, resource=resource, category=category, observed_at=observed,
                    time_basis="recorded_at" if observed else "unknown", claim_kind="RECORD_SNAPSHOT"))
                parsed += int(observed is not None)
                continue
        elif stripped in {"CUSTOMER PLATFORM - SHIFT HANDOVER", "Account and downstream checks completed during the shift:"}:
            continue
        else:
            seen += 1
        diagnostics.append(ParseDiagnostic("UNPARSED_TEXT", location, "narrative retained for later extraction"))
        observations.append(make_observation(source, digest, location, {"raw_line": raw},
            observed_at=clock, time_basis="snapshot" if clock else "unknown", claim_kind="RAW_UNPARSED"))
    return finish(source, "text", digest, observations, diagnostics, seen, parsed)
