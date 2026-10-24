from dataclasses import replace
import json

import pytest

from fixtures.history_cases import at, observation
from ghosttrace.resolve.temporal_replay import replay


def facts(state):
    return {f.dimension: json.loads(f.value_json) if f.value_json is not None else None for f in state.facts}


def test_later_operation_success_does_not_replace_a_direct_readback():
    present = observation("read", {"event": "profile_lookup_completed", "rows": 1}, kind="LOG_EVENT", day=8)
    deleted = observation("delete", {"event_type": "DELETE_RECORD", "reported_result": "SUCCESS"}, kind="OPERATION_CLAIM", day=9)
    restored = observation("restore", {"event_type": "RESTORE_BACKUP", "reported_result": "SUCCESS"}, kind="OPERATION_CLAIM", day=10)
    state, = replay([present, deleted, restored], at(20))
    assert facts(state)["presence"] == "PRESENT" and len(state.timeline) == 3
    assert state.facts[0].observation_ids == (present.observation_id,)


def test_claims_alone_and_empty_inventory_do_not_prove_absence():
    claim = observation("delete", {"reported_result": "SUCCESS"}, kind="OPERATION_CLAIM")
    state, = replay([claim], at(20))
    assert not state.facts and state.uncertainties[0].code == "STATE_NOT_ESTABLISHED"
    scope = observation("scope", {"row_count": 0}, kind="SCOPE_METADATA", resource="")
    assert replay([scope], at(20)) == ()


def test_explicit_resource_readback_proves_scoped_absence_and_recreation():
    missing = observation("missing", {"event": "profile_lookup_completed", "rows": "0"}, kind="LOG_EVENT", day=10)
    recreated = observation("recreated", {"email": "person@example.invalid"}, day=12)
    assert facts(replay([missing, recreated], at(11))[0])["presence"] == "ABSENT"
    assert facts(replay([missing, recreated], at(12))[0])["presence"] == "PRESENT"


def test_both_capture_and_observation_clocks_filter_state():
    present = observation("eligible", {"email": "person@example.invalid"}, day=10)
    later_event = observation("future", {"result": "NOT_FOUND"}, day=21)
    late_capture = observation("late", {"result": "NOT_FOUND"}, day=11, available=21)
    unknown = replace(observation("unknown", {"result": "NOT_FOUND"}), observed_at=None)
    assert facts(replay([present, later_event, late_capture, unknown], at(20))[0])["presence"] == "PRESENT"


def test_replicas_and_systems_with_same_resource_id_remain_separate():
    primary = observation("primary", {"result": "NOT_FOUND"}, copy="primary")
    replica = observation("replica", {"email": "person@example.invalid"}, copy="replica")
    other = observation("other", {"result": "NOT_FOUND"}, system="different", copy="replica")
    states = replay([primary, replica, other], at(20))
    actual = {(s.resource.system_id, s.resource.physical_copy): facts(s)["presence"] for s in states}
    assert actual == {("svc", "primary"): "ABSENT", ("svc", "replica"): "PRESENT", ("different", "replica"): "ABSENT"}


def test_simultaneous_conflict_is_preserved_without_format_or_id_priority():
    first = observation("z-json", {"result": "NOT_FOUND"})
    second = observation("a-sql", {"record": {"email": "person@example.invalid"}}, kind="SQL_RECORD")
    state, = replay([first, second], at(20))
    assert state == replay([second, first], at(20))[0]
    presence = next(f for f in state.facts if f.dimension == "presence")
    assert presence.value_json is None
    assert set(presence.conflicting_values) == {'"ABSENT"', '"PRESENT"'}
    assert {u.code for u in state.uncertainties} == {"CONFLICTING_STATE"}


def test_later_direct_observation_supersedes_old_state_with_its_own_proof():
    first = observation("present", {"email": "before@example.invalid"}, day=10)
    second = observation("redacted", {"email": None}, day=11)
    state, = replay([first, second], at(20))
    assert facts(state)["/email"] is None
    field = next(f for f in state.facts if f.dimension == "/email")
    assert field.value_json == "null" and field.observation_ids == (second.observation_id,)


@pytest.mark.parametrize("value,expected", [(False, False), ("false", False), ("true", True), (True, True)])
def test_named_boolean_flags_preserve_false(value, expected):
    state, = replay([observation("flag", {"event": "connector_config_loaded", "enabled": value}, kind="LOG_EVENT")], at(20))
    assert facts(state)["/enabled"] is expected


@pytest.mark.parametrize("value", [0, 1, "yes", "", None, []])
def test_unrecognized_boolean_values_do_not_become_process_state(value):
    state, = replay([observation("flag", {"enabled": value})], at(20))
    assert "/enabled" not in facts(state)


def test_cache_miss_and_started_query_cannot_establish_absence():
    cache = observation("cache", {"event": "cache_lookup", "result": "miss"}, kind="LOG_EVENT")
    started = observation("start", {"event": "profile_lookup_started", "rows": 0}, kind="LOG_EVENT")
    assert not replay([cache, started], at(20))[0].facts


def test_boolean_row_count_is_not_interpreted_as_integer_zero():
    state, = replay([observation("count", {"event": "profile_lookup_completed", "rows": False}, kind="LOG_EVENT")], at(20))
    # An invalid count cannot supply either positive or negative row evidence.
    assert not state.facts


def test_long_numeric_row_count_is_bounded_by_presence_semantics():
    state, = replay([observation("count", {"event": "profile_lookup_completed", "rows": "9" * 5000}, kind="LOG_EVENT")], at(20))
    assert facts(state)["presence"] == "PRESENT"


def test_field_omission_and_later_absence_do_not_assert_redaction_or_old_pii():
    before = observation("before", {"email": "before@example.invalid"}, day=9)
    for later in [observation("omitted", {"user_id": "subject-A"}, day=10),
                  observation("absent", {"event": "profile_lookup_completed", "rows": 0}, day=10, kind="LOG_EVENT")]:
        state, = replay([before, later], at(20))
        email = next(f for f in state.facts if f.dimension == "/email")
        assert email.value_json is None and not email.conflicting_values
        assert email.observation_ids == (later.observation_id,)
        assert "FIELD_NOT_OBSERVED_IN_LATEST_STATE" in {u.code for u in state.uncertainties}


def test_inconsistent_query_count_and_returned_documents_remain_conflicting():
    state, = replay([observation("query", {"hits": {"total": 0, "documents": [{"email": "a@example.invalid"}]}})], at(20))
    assert next(f for f in state.facts if f.dimension == "presence").value_json is None


def test_restore_deny_is_a_process_fact_and_archive_remains_present():
    state, = replay([observation("restore", {"event": "restore_policy_read_completed",
        "archive_present": True, "restore_allowed": False}, kind="LOG_EVENT")], at(20))
    assert facts(state) == {"/archive_present": True, "/restore_allowed": False, "presence": "PRESENT"}


def test_naive_cutoff_is_rejected():
    with pytest.raises(ValueError): replay([], at(20).replace(tzinfo=None))
