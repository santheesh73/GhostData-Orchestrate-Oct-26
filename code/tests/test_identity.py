from dataclasses import replace

import pytest

from fixtures.history_cases import at, change, observation, request, snapshot
from ghosttrace.resolve.identity_graph import IdentityGraph


def resolve(observations, **kwargs):
    r = request(**kwargs)
    return IdentityGraph(observations).at(r.audit_at).resolve(r)


def test_historical_email_chain_has_half_open_ownership_and_provenance():
    observations = [snapshot(email="third@example.invalid"), change(day=10),
                    change("later", old="new@example.invalid", new="third@example.invalid", day=15)]
    view = IdentityGraph(observations).at(at(20))
    assert {o.user_id for o in view.owners("email", "OLD@EXAMPLE.INVALID", at=at(9))} == {"subject-A"}
    assert not view.owners("email", "old@example.invalid", at=at(10))
    assert {o.user_id for o in view.owners("email", "new@example.invalid", at=at(10))} == {"subject-A"}
    assert not view.owners("email", "new@example.invalid", at=at(15))
    result = resolve(observations)
    assert result.status == "RESOLVED" and result.user_id == "subject-A"
    old = next(o for o in result.ownership if o.value == "old@example.invalid")
    assert old.valid_until == at(10) and old.observation_ids == (observations[1].observation_id,)
    middle = next(o for o in result.ownership if o.value == "new@example.invalid")
    assert set(middle.observation_ids) == {observations[1].observation_id, observations[2].observation_id}
    assert middle.available_at == at(15)


def test_unique_historical_email_can_be_used_after_retirement():
    assert resolve([change()], submitted=15).status == "RESOLVED"


def test_reassigned_email_uses_request_time_without_unioning_people():
    shared = "shared@example.invalid"
    records = [change("leave", old=shared, new="a@example.invalid", day=10),
               change("join", user="subject-B", old="b@example.invalid", new=shared, day=10)]
    assert resolve(records, email=shared, submitted=9).user_id == "subject-A"
    assert resolve(records, email=shared, submitted=10).user_id == "subject-B"
    assert {o.user_id for o in IdentityGraph(records).at(at(20)).owners("email", shared)} == {"subject-A", "subject-B"}


def test_overlapping_owners_are_ambiguous_even_when_names_are_identical():
    records = [snapshot("subject-A", "old@example.invalid"), snapshot("subject-B", "old@example.invalid"),
               change(), change("other", user="subject-B")]
    result = resolve(records)
    assert result.status == "AMBIGUOUS" and result.user_id is None
    assert result.candidate_user_ids == ("subject-A", "subject-B")


def test_snapshot_update_time_is_not_assumed_to_be_availability():
    result = resolve([snapshot(email="old@example.invalid")])
    assert result.status == "CONTEXT_ONLY"
    assert {u.code for u in result.uncertainties} == {"SNAPSHOT_AVAILABILITY_UNKNOWN"}


def test_eligible_stable_reference_pair_corroborates_snapshot_candidate():
    records = [snapshot(email="old@example.invalid"), observation("pair", {
        "user_id": "subject-A", "email": "old@example.invalid"}, day=4)]
    result = resolve(records)
    assert result.status == "RESOLVED" and result.user_id == "subject-A"


def test_later_pair_is_not_lifelong_ownership_at_request_time():
    result = resolve([snapshot(email="old@example.invalid"), observation("pair", {
        "user_id": "subject-A", "email": "old@example.invalid"}, day=6)])
    assert result.status == "CONTEXT_ONLY"


def test_future_audit_does_not_reveal_old_email_before_cutoff():
    assert resolve([change(day=21)]).status == "UNRESOLVED"
    assert resolve([change(day=20)]).status == "RESOLVED"


def test_future_subject_registry_entry_cannot_reinterpret_an_earlier_reference():
    earlier = observation("earlier", {"customer_reference": "not-yet-registered",
                                      "email": "old@example.invalid"}, day=4)
    later = change("future-registry", user="not-yet-registered", day=21)
    assert resolve([earlier]).status == resolve([earlier, later]).status == "UNRESOLVED"


def test_late_capture_and_unknown_time_cannot_supply_identity_proof():
    late = replace(change(), evidence=replace(change().evidence, available_at=at(21)))
    unknown = replace(change("unknown"), observed_at=None)
    assert resolve([late, unknown]).status == "UNRESOLVED"


def test_started_query_is_not_a_stable_identifier_ownership_observation():
    record = observation("start", {"event": "profile_lookup_started", "user_id": "subject-A",
                                   "email": "old@example.invalid"}, kind="LOG_EVENT", day=4)
    assert resolve([record]).status == "UNRESOLVED"


def test_unrelated_nested_email_is_not_paired_with_an_envelope_user_id():
    record = observation("envelope", {"user_id": "subject-A", "messages": [
        {"sender_email": "old@example.invalid", "body": "unrelated sender"}]}, day=4)
    assert resolve([record]).status == "UNRESOLVED"


def test_broken_history_is_not_repaired_by_current_snapshot():
    result = resolve([snapshot(), change(), change("gap", old="unseen@example.invalid", new="last@example.invalid", day=15)])
    assert result.status == "AMBIGUOUS"
    assert "BROKEN_IDENTITY_HISTORY" in {u.code for u in result.uncertainties}


def test_same_timestamp_disagreement_remains_uncertain_and_order_independent():
    records = [change(), change("conflict", new="other@example.invalid")]
    first = resolve(records)
    assert first == resolve(records[::-1])
    assert first.status == "AMBIGUOUS"
    assert "CONFLICTING_IDENTITY_HISTORY" in {u.code for u in first.uncertainties}


def test_duplicate_consistent_changes_combine_proofs_without_creating_a_conflict():
    records = [change(), change("corroboration")]
    result = resolve(records)
    assert result.status == "RESOLVED"
    assert len(next(o for o in result.ownership if o.value == "old@example.invalid").observation_ids) == 2


def test_names_near_emails_and_untyped_tokens_do_not_establish_ownership():
    records = [snapshot(), observation("text", {"name": "Same Display Name",
        "details": "old@example.invalid belongs to subject-A", "email": "olds@example.invalid"})]
    assert resolve(records).status == "UNRESOLVED"


def test_phone_and_hash_have_separate_normalized_ownership_namespaces():
    records = [change(kind="phone", old="+47 123-456", new="+47 999-999"),
               change("hash", kind="email_hash", old="ABC", new="DEF")]
    view = IdentityGraph(records).at(at(20))
    assert view.owners("phone", "+47123456")[0].user_id == "subject-A"
    assert view.owners("email_hash", "abc")[0].user_id == "subject-A"
    assert not view.owners("email", "abc")


def test_naive_or_inconsistent_request_clocks_are_rejected():
    graph = IdentityGraph([change()])
    with pytest.raises(ValueError): graph.at(at(20).replace(tzinfo=None))
    with pytest.raises(ValueError): graph.at(at(20)).resolve(request(cutoff=19))
    with pytest.raises(ValueError): graph.at(at(20)).resolve(request(submitted=21))
