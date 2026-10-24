"""Generic participant evidence CSV adapter; retain cells as strings."""

import csv
import io

from .normalization import (MAX_UNITS, ParseDiagnostic, finish,
                            make_observation, observation_time)


def parse_csv(text, source, digest):
    reader = csv.reader(io.StringIO(text), strict=True)
    header = next(reader, None)
    if not header or len(set(header)) != len(header) or any(not name.strip() for name in header):
        raise ValueError("CSV evidence requires unique nonempty column names")
    observations, diagnostics = [], []
    seen = parsed = 0
    for ordinal, cells in enumerate(reader, 1):
        seen += 1
        if seen > MAX_UNITS:
            raise ValueError("CSV evidence row budget exceeded")
        location = f"record:{ordinal}"
        if len(cells) != len(header):
            diagnostics.append(ParseDiagnostic("RAGGED_CSV_RECORD", location, "record width differs from header", "ERROR"))
            payload, kind = {"columns": header, "cells": cells}, "RAW_UNPARSED"
        else:
            payload, kind = dict(zip(header, cells)), "CSV_RECORD"
            parsed += 1
        clock, basis = observation_time(payload, source.available_at,
            "file_capture" if source.available_at else "unknown", diagnostics, location)
        observations.append(make_observation(source, digest, location, payload,
            system=payload.get("system_id", payload.get("system", payload.get("origin_system", ""))),
            resource=payload.get("resource_id", ""), category=payload.get("record_type", ""),
            observed_at=clock, time_basis=basis, claim_kind=kind))
    return finish(source, "csv", digest, observations, diagnostics, seen, parsed)
