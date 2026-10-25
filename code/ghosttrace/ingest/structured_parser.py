"""Manifest routing and explicit per-file accounting. No labels are read."""

import hashlib
from pathlib import Path, PurePosixPath, PureWindowsPath
import csv
import re
import sqlite3

from ..models import EvidenceSource
from .json_parser import parse_json_document
from .loader import InputError, parse_timestamp, read_records
from .log_parser import parse_log, parse_text
from .normalization import (MAX_FILE_BYTES, MAX_UNITS, ParseDiagnostic, ParseResult, ParseStatus,
                            finish, make_observation)
from .sql_parser import parse_sql
from .csv_parser import parse_csv


def load_manifest(dataset_root: Path) -> tuple[EvidenceSource, ...]:
    records = read_records(dataset_root / "evidence_files.csv",
                           ("file_id", "file_path", "origin", "captured_at"))
    if not records:
        raise InputError("evidence manifest contains no files")
    sources, seen = [], set()
    for number, row in enumerate(records, 2):
        if any(not value.strip() for value in row.values()) or row["file_id"] in seen:
            raise InputError(f"manifest row {number}: blank metadata or duplicate ID")
        if row["file_id"] != row["file_id"].strip():
            raise InputError(f"manifest row {number}: padded evidence ID")
        seen.add(row["file_id"])
        sources.append(EvidenceSource(row["file_id"], parse_timestamp(row["captured_at"], "captured_at"),
                                      row["origin"], row["file_path"]))
    return tuple(sources)


def evidence_path(dataset_root: Path, relative: str) -> Path:
    portable = PurePosixPath(relative.replace("\\", "/"))
    if ("\x00" in relative or portable.is_absolute() or PureWindowsPath(relative).drive
            or ".." in portable.parts or not portable.parts or portable.parts[0] != "evidence"):
        raise ValueError("manifest path must stay inside participant evidence/")
    base = dataset_root.resolve()
    candidate = base.joinpath(*portable.parts).resolve()
    if not candidate.is_relative_to(base / "evidence"):
        raise ValueError("manifest path escapes evidence/ through a link")
    return candidate


def parse_source(dataset_root: Path, source: EvidenceSource) -> ParseResult:
    digest, format_name = "", Path(source.path).suffix.lower().lstrip(".")
    if format_name == "txt":
        format_name = "text"
    try:
        path = evidence_path(dataset_root, source.path)
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("evidence file exceeds supported size")
        digest = hashlib.sha256(data).hexdigest()
        if format_name in {"pdf", "png", "jpg", "jpeg"}:
            return ParseResult(source, format_name, ParseStatus.DEFERRED, digest, diagnostics=(
                ParseDiagnostic("DOCUMENT_EXTRACTION_DEFERRED", "file", "document/vision extraction is deferred to Phase 05"),))
        if not data:
            return ParseResult(source, format_name, ParseStatus.EMPTY, digest)
        text = data.decode("utf-8-sig")
        if "\x00" in text:
            raise ValueError("text evidence contains NUL characters")
        if format_name == "json":
            return parse_json_document(text, source, digest)
        if format_name == "sql":
            return parse_sql(text, source, digest)
        if format_name == "log":
            return parse_log(text, source, digest)
        if format_name == "text":
            return parse_text(text, source, digest)
        if format_name == "csv":
            return parse_csv(text, source, digest)
        return ParseResult(source, format_name, ParseStatus.DEFERRED, digest, diagnostics=(
            ParseDiagnostic("UNSUPPORTED_FORMAT", "file", "no adapter is configured for this format"),))
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError, sqlite3.Error, csv.Error) as exc:
        # Avoid echoing raw records, SQL values, paths outside the manifest, or PII.
        return ParseResult(source, format_name, ParseStatus.FAILED, digest, diagnostics=(
            ParseDiagnostic("SOURCE_PARSE_FAILED", "file", f"source could not be safely parsed ({type(exc).__name__})", "ERROR"),))


def load_context_sources(dataset_root: Path) -> tuple[ParseResult, ...]:
    """Context snapshots are non-citeable; audit/activity rows retain real IDs."""
    results = []
    definitions = (
        ("user_identities.csv", ("user_id", "name", "email", "phone", "email_hash", "updated_at"), "updated_at", None, "IDENTITY_REGISTRY_ENTRY"),
        ("user_audit_log.csv", ("audit_id", "user_id", "event_time", "field_name", "old_value", "new_value"), "event_time", "audit_id", "IDENTITY_CHANGE_CLAIM"),
        ("system_activity.csv", ("activity_id", "event_time", "event_type", "source_system", "target_system", "resource_id", "reported_result", "details"), "event_time", "activity_id", "OPERATION_CLAIM"),
        ("deletion_rules.csv", ("rule_id", "data_category", "condition", "required_action"), None, None, "POLICY_CONTEXT"),
    )
    for filename, columns, time_key, id_key, kind in definitions:
        container = EvidenceSource(filename, None, "context_csv", filename, False)
        digest = ""
        try:
            path = dataset_root / filename
            if not path.resolve().is_relative_to(dataset_root.resolve()):
                raise ValueError("context source escapes dataset root")
            with path.open("rb") as stream:
                data = stream.read(MAX_FILE_BYTES + 1)
            if len(data) > MAX_FILE_BYTES:
                raise ValueError("context file exceeds supported size")
            digest = hashlib.sha256(data).hexdigest()
            records = read_records(path, columns)
            if len(records) > MAX_UNITS:
                raise ValueError("context row budget exceeded")
            observations, diagnostics, ids = [], [], set()
            parsed = 0
            for line, record in enumerate(records, 2):
                location = f"line:{line}"
                before = len(diagnostics)
                clock = None
                if time_key:
                    try:
                        clock = parse_timestamp(record[time_key], time_key)
                    except InputError:
                        diagnostics.append(ParseDiagnostic("INVALID_TIMESTAMP", location, "invalid CSV timestamp", "ERROR"))
                source = container
                if id_key:
                    value = record[id_key]
                    if not value.strip() or value != value.strip() or value in ids:
                        diagnostics.append(ParseDiagnostic("INVALID_EVIDENCE_ID", location, "blank, padded, or duplicate event ID", "ERROR"))
                    ids.add(value)
                    source = EvidenceSource(value, clock, kind, filename)
                values = dict(record)
                if kind == "OPERATION_CLAIM" and record.get("event_type") == "LINK_RESOURCE_IDENTITY":
                    match = re.fullmatch(r"Data catalog linked (\S+) \(([^()]*)\) to (\S+) and (\S+)\.", record["details"])
                    if match and match[1] == record["resource_id"] and match[2] == match[4]:
                        values.update(catalog_subject_reference=match[4], catalog_email=match[3])
                    attachment = re.fullmatch(r"Attachment catalog confirmed (\S+) \(([^()]*)\) belongs only to (\S+) and (\S+); no other subject is linked\.", record["details"])
                    if attachment and attachment[1] == record["resource_id"]:
                        values.update(catalog_subject_reference=attachment[4], catalog_email=attachment[3], catalog_sole_subject=True,
                                      catalog_filename=attachment[2])
                observations.append(make_observation(source, digest, location, values,
                    system=record.get("target_system", ""), resource=record.get("resource_id", ""),
                    category=record.get("data_category", ""), observed_at=clock,
                    time_basis=time_key or "unknown", claim_kind=kind))
                parsed += int(len(diagnostics) == before)
            results.append(finish(container, "csv", digest, observations, diagnostics, len(records), parsed))
        except (OSError, UnicodeError, ValueError) as exc:
            results.append(ParseResult(container, "csv", ParseStatus.FAILED, digest, diagnostics=(
                ParseDiagnostic("CONTEXT_PARSE_FAILED", "file", f"context source failed ({type(exc).__name__})", "ERROR"),)))
    return tuple(results)
