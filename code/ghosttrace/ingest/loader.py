"""Strict CSV boundaries. Metadata loading does not inspect evidence contents."""

import csv
from datetime import datetime, timezone
from pathlib import Path

from ..models import EvidenceSource, Request
from ..spec_registry import REQUEST_COLUMNS


class InputError(ValueError):
    """An input contract violation; messages avoid echoing personal fields."""


def parse_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or "T" not in value:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        raise InputError(f"{label}: expected an ISO-8601 timestamp with timezone") from None


def read_records(path: Path, columns: tuple[str, ...], *, exact: bool = True) -> list[dict]:
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            header = next(reader, None)
            if header is None or len(header) != len(set(header)):
                raise InputError(f"{path.name}: missing or duplicate header")
            if (exact and tuple(header) != columns) or not set(columns) <= set(header):
                raise InputError(f"{path.name}: unexpected columns; required {','.join(columns)}")
            records = []
            for number, values in enumerate(reader, 2):
                if len(values) != len(header) or any("\x00" in v for v in values):
                    raise InputError(f"{path.name}: malformed CSV row {number}")
                records.append(dict(zip(header, values)))
            return records
    except (OSError, UnicodeError, csv.Error) as exc:
        raise InputError(f"{path.name}: cannot read valid UTF-8 CSV ({type(exc).__name__})") from None


def load_requests(path: Path) -> tuple[Request, ...]:
    records = read_records(Path(path), REQUEST_COLUMNS)
    if not records:
        raise InputError("request input contains no cases")
    requests, seen = [], set()
    for number, row in enumerate(records, 2):
        if any(not row[k].strip() for k in REQUEST_COLUMNS):
            raise InputError(f"request row {number}: required field is blank")
        case_id = row["case_id"]
        if case_id != case_id.strip() or case_id in seen:
            raise InputError(f"request row {number}: duplicate or padded case_id")
        seen.add(case_id)
        if row["reported_status"] not in {"COMPLETE", "PARTIALLY_COMPLETE", "NOT_STARTED"}:
            raise InputError(f"request row {number}: invalid reported_status")
        requests.append(Request(
            case_id, row["email"], parse_timestamp(row["requested_at"], "requested_at"),
            row["reported_status"], parse_timestamp(row["reported_at"], "reported_at"),
            parse_timestamp(row["audit_at"], "audit_at"), row["request_text"],
        ))
    return tuple(requests)


def load_evidence_catalog(dataset_root: Path) -> dict[str, EvidenceSource]:
    """IDs and availability only; membership/support are NOT verified here."""
    catalog = {}
    for filename, id_column, time_column in (
        ("evidence_files.csv", "file_id", "captured_at"),
        ("system_activity.csv", "activity_id", "event_time"),
        ("user_audit_log.csv", "audit_id", "event_time"),
    ):
        for number, row in enumerate(read_records(
                dataset_root / filename, (id_column, time_column), exact=False), 2):
            evidence_id = row[id_column]
            if not evidence_id.strip() or evidence_id != evidence_id.strip() or evidence_id in catalog:
                raise InputError(f"{filename} row {number}: blank, padded, or duplicate evidence ID")
            catalog[evidence_id] = EvidenceSource(
                evidence_id, parse_timestamp(row[time_column], time_column), filename,
                row.get("file_path", ""),
            )
    return catalog
