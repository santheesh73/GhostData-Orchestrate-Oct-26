"""Handwritten subjects and times; no public labels or challenge ID families."""

from datetime import datetime, timedelta, timezone

from ghosttrace.ingest.normalization import make_observation
from ghosttrace.models import EvidenceSource, Request

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def at(day):
    return START + timedelta(days=day)


def request(email="old@example.invalid", submitted=5, cutoff=20, case="opaque-case"):
    return Request(case, email, at(submitted), "COMPLETE", at(submitted), at(cutoff), "Delete my account")


def observation(name, data, *, day=10, available=None, kind="RECORD_SNAPSHOT", system="svc",
                resource="record/opaque", copy="primary", trace="", file=None):
    source = EvidenceSource(file or name, at(day if available is None else available), "synthetic",
                            "evidence/synthetic.json")
    return make_observation(source, "synthetic-sha", name, data, observed_at=at(day),
        system=system, resource=resource, physical_copy=copy, claim_kind=kind, trace_id=trace,
        time_basis="observed_at")


def snapshot(user="subject-A", email="new@example.invalid", **fields):
    source = EvidenceSource("user_identities.csv", None, "context", "user_identities.csv", False)
    return make_observation(source, "synthetic-sha", user,
        dict(user_id=user, email=email, name="Same Display Name", **fields),
        claim_kind="IDENTITY_CONTEXT", observed_at=at(0), time_basis="updated_at")


def change(name="change", user="subject-A", old="old@example.invalid", new="new@example.invalid", day=10, kind="email"):
    return observation(name, dict(user_id=user, field_name=kind, old_value=old, new_value=new),
                       day=day, kind="IDENTITY_CHANGE_CLAIM", resource="", system="", copy="")
