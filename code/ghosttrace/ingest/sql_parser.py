"""Read SQLite dump snapshots inside a restricted, ephemeral in-memory database.

Only table/index dump DDL, INSERT/transaction statements, and foreign_keys=ON are accepted.
An authorizer denies attachment, extensions, virtual tables, triggers, arbitrary
functions, and host-file pragmas. Statement and VM budgets bound execution.
No participant database or filesystem path is opened by SQLite.
"""

import re
import sqlite3
from contextlib import closing

from .json_parser import COLLECTION_SYSTEM
from .loader import InputError, parse_timestamp
from .normalization import (MAX_FILE_BYTES, MAX_UNITS, ParseDiagnostic, finish,
                            make_observation, strict_json)


def _without_leading_comments(text):
    while True:
        stripped = re.sub(r'^\s*(?:--[^\n]*(?:\n|$)|/\*.*?\*/)', '', text, count=1, flags=re.S)
        if stripped == text:
            return text.strip()
        text = stripped


def _statements(text):
    start = 0
    for end, character in enumerate(text):
        if character == ";" and sqlite3.complete_statement(text[start:end + 1]):
            yield text[start:end + 1]
            start = end + 1
    if _without_leading_comments(text[start:]):
        raise ValueError("SQL has an incomplete trailing statement")


def _authorize(action, arg1, arg2, database, trigger):
    allowed = {sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_INSERT, sqlite3.SQLITE_READ,
               sqlite3.SQLITE_SELECT, sqlite3.SQLITE_TRANSACTION}
    if database not in (None, "main") or trigger is not None:
        return sqlite3.SQLITE_DENY
    if action in allowed:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_UPDATE and arg1 in {"sqlite_master", "sqlite_schema"}:
        return sqlite3.SQLITE_OK
    if action in {sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_REINDEX}:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() == "json_valid":
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_PRAGMA and arg1 == "foreign_keys" and (arg2 or "").upper() == "ON":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def parse_sql(text, source, digest):
    observations, diagnostics = [], []
    seen = parsed = 0
    clock, basis = source.available_at, "file_capture" if source.available_at else "unknown"
    header = re.search(r'^--\s*Captured at:\s*(\S+)', text, re.M)
    if header:
        try:
            clock, basis = parse_timestamp(header[1], "SQL capture"), "snapshot_header"
        except InputError:
            diagnostics.append(ParseDiagnostic("INVALID_TIMESTAMP", "header", "invalid SQL capture time", "ERROR"))
            clock, basis = None, "unknown"
    with closing(sqlite3.connect(":memory:", isolation_level=None)) as connection:
        connection.execute("PRAGMA temp_store=MEMORY")
        connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_FILE_BYTES)
        connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, MAX_FILE_BYTES)
        connection.set_authorizer(_authorize)
        calls = 0
        def bounded_progress():
            nonlocal calls
            calls += 1
            return int(calls > 1000)  # JUDGEMENT: at most about one million VM operations/file.
        connection.set_progress_handler(bounded_progress, 1000)
        for ordinal, statement in enumerate(_statements(text), 1):
            if ordinal > MAX_UNITS:
                raise ValueError("SQL statement budget exceeded")
            stripped = _without_leading_comments(statement)
            if not stripped:
                continue
            accepted = re.match(r'^(?:BEGIN(?:\s+TRANSACTION)?\s*;|COMMIT\s*;|CREATE\s+(?:TABLE|(?:UNIQUE\s+)?INDEX)\s|INSERT\s+INTO\s)', stripped, re.I)
            foreign_keys = re.fullmatch(r'PRAGMA\s+foreign_keys\s*=\s*ON\s*;', stripped, re.I)
            if not accepted and not foreign_keys:
                raise ValueError(f"unsupported SQL dump statement {ordinal}")
            connection.execute(stripped)
        if connection.in_transaction:
            raise ValueError("SQL snapshot ends with an uncommitted transaction")
        tables = connection.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        if not tables:
            raise ValueError("SQL snapshot contains no tables")
        comments = [{"line": n, "text": line} for n, line in enumerate(text.splitlines(), 1)
                    if line.lstrip().startswith("--")]
        if comments:
            seen += 1
            parsed += 1
            observations.append(make_observation(source, digest, "@metadata", {"comments": comments},
                observed_at=clock, time_basis=basis, claim_kind="FILE_METADATA"))
        scopes = {}
        if any(name == "snapshot_scope" for name, _ in tables):
            cursor = connection.execute('SELECT * FROM "snapshot_scope"')
            if {"origin_system", "captured_at"} <= {d[0] for d in cursor.description}:
                for values in cursor.fetchall():
                    scope = dict(zip([d[0] for d in cursor.description], values))
                    try:
                        scopes[scope["origin_system"]] = parse_timestamp(scope["captured_at"], "snapshot scope")
                    except InputError:
                        scopes[scope["origin_system"]] = None
                        diagnostics.append(ParseDiagnostic("INVALID_TIMESTAMP", "table:snapshot_scope", "invalid scope capture timestamp", "ERROR"))
        for table, schema in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            cursor = connection.execute("SELECT * FROM " + quoted)
            columns = [d[0] for d in cursor.description]
            records = cursor.fetchmany(MAX_UNITS + 1)
            if len(records) > MAX_UNITS:
                raise ValueError("SQL row budget exceeded")
            seen += 1
            parsed += 1
            observations.append(make_observation(source, digest, f"table:{table}/@scope",
                {"table": table, "schema": schema, "columns": columns, "rows_observed": len(records),
                 "completeness": "NOT_ESTABLISHED"}, category="TABLE_SCOPE", physical_copy=table,
                observed_at=clock, time_basis=basis, claim_kind="SCOPE_METADATA"))
            for ordinal, values in enumerate(records, 1):
                seen += 1
                if seen > MAX_UNITS:
                    raise ValueError("SQL total row budget exceeded")
                location = f"table:{table}/row:{ordinal}"
                row = dict(zip(columns, values))
                payload = dict(row)
                valid_record = True
                if "record_json" in row:
                    try:
                        record = strict_json(row["record_json"])
                        if not isinstance(record, dict):
                            raise ValueError("record_json must be an object")
                        payload["record"] = record
                    except (ValueError, TypeError, RecursionError):
                        valid_record = False
                        diagnostics.append(ParseDiagnostic("INVALID_RECORD_JSON", location,
                                                           "embedded record retained but not decoded", "ERROR"))
                system = row.get("origin_system", COLLECTION_SYSTEM.get(table, ""))
                if not isinstance(system, str):
                    system = ""
                    valid_record = False
                    diagnostics.append(ParseDiagnostic("INVALID_RESOURCE_CONTEXT", location, "system identifier must be a string", "ERROR"))
                resource = row.get("resource_id", "")
                if not isinstance(resource, str):
                    resource = ""
                    valid_record = False
                    diagnostics.append(ParseDiagnostic("INVALID_RESOURCE_CONTEXT", location, "resource identifier must be a string", "ERROR"))
                observed = scopes.get(system, clock)
                observed_basis = "snapshot_scope" if system in scopes else basis
                observations.append(make_observation(source, digest, location, payload,
                    system=system, resource=resource,
                    category=str(row.get("collection_name", table)), physical_copy=table,
                    observed_at=observed, time_basis=observed_basis,
                    claim_kind="SQL_RECORD" if valid_record else "RAW_UNPARSED"))
                parsed += int(valid_record)
    return finish(source, "sql", digest, observations, diagnostics, seen, parsed)
