from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from ghosttrace.ingest.evidence_index import EvidenceIndex
from ghosttrace.ingest.normalization import make_observation
from ghosttrace.models import EvidenceSource

TIME = datetime(2026, 1, 2, tzinfo=timezone.utc)


def observation(location="row:1", **changes):
    source = EvidenceSource("synthetic_file", TIME, "synthetic", "evidence/example.json")
    return make_observation(source, "digest", location,
        {"resource_id": "opaque", "email": "PERSON@Example.invalid", "phone": "+47 12-34 56",
         "name": "Shared Name", "email_hash": "ABCDEF"}, system="svc", resource="opaque",
        observed_at=TIME, time_basis="observed_at", **changes)


def test_exact_candidate_lookup_normalizes_without_fuzzy_identity_merges():
    index = EvidenceIndex([observation()])
    assert len(index.lookup_identifier("email", "person@example.invalid").observations) == 1
    assert len(index.lookup_identifier("phone", "+47123456").observations) == 1
    assert len(index.lookup_identifier("email_hash", "abcdef").observations) == 1
    assert not index.lookup_identifier("email", "persons@example.invalid").observations
    assert not index.lookup_identifier("name", "Shared").observations


def test_resource_and_evidence_queries_preserve_distinct_copies():
    primary = observation(physical_copy="primary")
    replica = observation(physical_copy="replica")
    other = replace(observation("row:2"), resource=replace(primary.resource, system_id="other"))
    index = EvidenceIndex([primary, replica, other])
    assert len(index.lookup_resource("opaque").observations) == 3
    assert len(index.lookup_resource("opaque", system_id="svc").observations) == 2
    assert index.lookup_resource("opaque", physical_copy="primary", system_id="svc").observations == (primary,)
    assert len(index.lookup_evidence("synthetic_file").observations) == 3


def test_index_is_idempotent_but_does_not_deduplicate_separate_source_locations():
    first, second = observation("row:1"), observation("row:2")
    index = EvidenceIndex([first, first, second])
    assert len(index) == 2
    assert index.all_observations() == EvidenceIndex([second, first]).all_observations()
    with pytest.raises(ValueError): index.add(replace(first, location="different"))


def test_cutoff_filters_both_capture_and_observation_times_and_reports_unknowns():
    current = observation()
    later_capture = replace(observation("row:2"), evidence=replace(current.evidence, available_at=TIME + timedelta(seconds=1)))
    later_event = replace(observation("row:3"), observed_at=TIME + timedelta(seconds=1))
    unknown = replace(observation("row:4"), observed_at=None)
    index = EvidenceIndex([current, later_capture, later_event, unknown])
    result = index.lookup_resource("opaque", at=TIME)
    assert result.observations == (current,)
    assert result.excluded_future == 2
    assert result.excluded_unknown_time == 1
    assert result.supports_absence is False
    assert not index.lookup_resource("missing", at=TIME).supports_absence


def test_non_citeable_identity_snapshot_is_not_assumed_available_at_update_time():
    record = observation()
    record = replace(record, evidence=replace(record.evidence, available_at=None, citeable=False))
    result = EvidenceIndex([record]).lookup_identifier("email", "person@example.invalid", at=TIME)
    assert not result.observations
    assert result.excluded_unknown_time == 1


def test_naive_retrieval_cutoff_is_rejected():
    with pytest.raises(ValueError): EvidenceIndex([observation()]).lookup_resource("opaque", at=datetime(2026, 1, 1))


def test_provenance_identity_binds_manifest_metadata_as_well_as_bytes():
    first = observation()
    changed_source = replace(first.evidence, available_at=TIME + timedelta(seconds=1))
    changed = make_observation(changed_source, "digest", first.location,
                              __import__('json').loads(first.payload_json), system="svc", resource="opaque",
                              observed_at=TIME, time_basis="observed_at")
    assert first.observation_id != changed.observation_id
