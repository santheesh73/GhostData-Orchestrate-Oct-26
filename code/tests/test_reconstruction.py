from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from fixtures.history_cases import at, change, observation, request, snapshot
from ghosttrace.ingest.evidence_index import EvidenceIndex
from ghosttrace.resolve.engine import ReconstructionEngine, proof_fingerprint, reconstruction_summary


def reconstruct(observations, **kwargs):
    return ReconstructionEngine(EvidenceIndex(observations)).reconstruct(request(**kwargs))


def test_historical_identifier_finds_multiple_accounts_with_same_stable_subject():
    observations = [change(), observation("old-account", {"email": "old@example.invalid"}, resource="account-A"),
        observation("new-account", {"user_id": "subject-A", "email": "new@example.invalid"}, resource="account-B")]
    result = reconstruct(observations)
    assert result.identity.user_id == "subject-A"
    assert {(link.resource_id, link.status) for link in result.links} == {("account-A", "LINKED"), ("account-B", "LINKED")}
    assert len(result.states) == 2


def test_stable_subject_prevents_stale_email_from_linking_another_person():
    observations = [change(), observation("different", {"email": "old@example.invalid", "user_id": "subject-B"})]
    # Request-time audit interval establishes A; explicit record ownership says B.
    result = reconstruct(observations)
    assert result.identity.user_id == "subject-A"
    assert not result.links and not result.states


def test_reused_alias_without_stable_reference_preserves_resource_ambiguity():
    records = [change(old="shared@example.invalid"),
        change("reuse", user="subject-B", old="b@example.invalid", new="shared@example.invalid", day=12),
        observation("stale-or-reassigned", {"email": "shared@example.invalid"}, day=14)]
    result = reconstruct(records, email="shared@example.invalid")
    assert result.identity.user_id == "subject-A"
    assert result.links[0].status == "AMBIGUOUS"
    assert result.links[0].user_ids == ("subject-A", "subject-B")
    assert {records[0].observation_id, records[1].observation_id, records[2].observation_id} <= set(result.links[0].observation_ids)


def test_alias_assignment_does_not_leak_back_into_older_resource_ownership():
    records = [change(old="shared@example.invalid"), snapshot("subject-B", "shared@example.invalid"),
        change("reuse", user="subject-B", old="b@example.invalid", new="shared@example.invalid", day=12),
        observation("before-reassignment", {"email": "shared@example.invalid"}, day=8)]
    result = reconstruct(records, email="shared@example.invalid")
    assert result.links[0].status == "LINKED" and result.links[0].user_ids == ("subject-A",)


def test_historical_resource_without_current_identifiers_uses_grounded_prior_link():
    records = [change(), observation("before", {"email": "old@example.invalid"}, day=8),
               observation("after", {"email": None, "name": None}, day=12)]
    result = reconstruct(records)
    assert len(result.links) == len(result.states) == 1
    field = next(f for f in result.states[0].facts if f.dimension == "/email")
    assert field.value_json == "null" and field.observation_ids == (records[2].observation_id,)


def test_unknown_snapshot_availability_cannot_become_a_confirmed_link():
    result = reconstruct([snapshot(email="old@example.invalid"), observation("record", {"email": "old@example.invalid"})])
    assert result.identity.status == "CONTEXT_ONLY"
    assert result.links[0].status == "PROVISIONAL"


def test_conflicting_stable_resource_owners_are_not_silently_reassigned():
    records = [change(), observation("first", {"user_id": "subject-A"}, day=8),
               observation("second", {"user_id": "subject-B"}, day=12)]
    result = reconstruct(records)
    assert result.links[0].status == "AMBIGUOUS"
    assert "AMBIGUOUS_RESOURCE_OWNER" in {u.code for u in result.uncertainties}


def test_trace_readback_inherits_lookup_target_with_all_link_proofs():
    start = observation("start", {"event": "profile_lookup_started", "lookup_key": "old@example.invalid"},
                        day=8, resource="", kind="LOG_EVENT", trace="trace", file="trace-file")
    end = observation("end", {"event": "profile_lookup_completed", "rows": 1},
                      day=9, resource="result", kind="LOG_EVENT", trace="trace", file="trace-file")
    result = reconstruct([change(), start, end])
    assert result.links[0].resource_id == "result" and result.links[0].status == "LINKED"
    assert {start.observation_id, end.observation_id} <= set(result.links[0].observation_ids)
    assert len(result.links[0].observation_ids) == 3  # lookup + readback + ownership audit


def test_trace_reuse_across_files_services_or_instances_does_not_link_subjects():
    start = observation("start", {"event": "profile_lookup_started", "lookup_key": "old@example.invalid"},
                        day=8, resource="", kind="LOG_EVENT", trace="trace", file="source-A")
    ends = [observation("other-file", {"event": "profile_lookup_completed", "rows": 1},
                day=9, kind="LOG_EVENT", trace="trace", file="source-B"),
            observation("other-instance", {"event": "profile_lookup_completed", "rows": 1},
                day=9, copy="replica", kind="LOG_EVENT", trace="trace", file="source-A"),
            observation("other-service", {"event": "profile_lookup_completed", "rows": 1},
                day=9, system="elsewhere", kind="LOG_EVENT", trace="trace", file="source-A")]
    assert not reconstruct([change(), start, *ends]).links


def test_later_trace_identity_cannot_explain_earlier_readback():
    end = observation("end", {"event": "profile_lookup_completed", "rows": 1},
                      day=8, kind="LOG_EVENT", trace="trace", file="trace-file")
    start = observation("start", {"event": "profile_lookup_started", "lookup_key": "old@example.invalid"},
                        day=9, resource="", kind="LOG_EVENT", trace="trace", file="trace-file")
    assert not reconstruct([change(), end, start]).links


def test_post_cutoff_events_cannot_change_proofs_or_resource_state():
    baseline = [change(), observation("before", {"user_id": "subject-A", "email": None}, day=12)]
    future = observation("future", {"user_id": "subject-A", "email": "old@example.invalid"}, day=21)
    late = observation("late", {"user_id": "subject-A", "email": "old@example.invalid"}, day=13, available=21)
    a, b = reconstruct(baseline), reconstruct([future, *baseline, late])
    assert proof_fingerprint(a) == proof_fingerprint(b)
    assert b.excluded_future == 2


def test_unrelated_resource_or_same_resource_in_other_system_does_not_join():
    records = [change(), observation("linked", {"email": "old@example.invalid"}),
               observation("unrelated", {"email": "someone@example.invalid"}, resource="other"),
               observation("same-id-other-system", {"email": "someone@example.invalid"}, system="other")]
    result = reconstruct(records)
    assert [(l.system_id, l.resource_id) for l in result.links] == [("svc", "record/opaque")]
    assert len(result.states) == 1


def test_catalog_link_is_a_provisional_claim_not_a_state_verdict():
    catalog = observation("catalog", {"event_type": "LINK_RESOURCE_IDENTITY", "reported_result": "SUCCESS",
        "details": "Data catalog linked catalog-only (subject-A) to old@example.invalid and subject-A."},
        resource="catalog-only", kind="OPERATION_CLAIM")
    result = reconstruct([change(), catalog])
    assert result.links[0].status == "PROVISIONAL" and not result.states[0].facts


def test_no_match_remains_unresolved_without_any_false_absence_state():
    result = reconstruct([observation("other", {"email": "someone@example.invalid"})])
    assert result.identity.status == "UNRESOLVED" and not result.states


def test_reversing_input_order_and_changing_opaque_ids_preserves_mechanism():
    records = [change(), observation("row", {"email": "old@example.invalid"})]
    assert proof_fingerprint(reconstruct(records)) == proof_fingerprint(reconstruct(records[::-1]))
    renamed = [change(user="arbitrary/stable@id"), observation("other-row", {"email": "old@example.invalid"},
                resource="random:string")]
    result = reconstruct(renamed, case="another-case")
    assert result.identity.user_id == "arbitrary/stable@id" and result.links[0].resource_id == "random:string"


def test_proof_is_identical_across_fresh_processes_and_hash_seeds():
    root = Path(__file__).resolve().parents[2]
    script = """
from fixtures.history_cases import change, observation, request
from ghosttrace.ingest.evidence_index import EvidenceIndex
from ghosttrace.resolve.engine import ReconstructionEngine, proof_fingerprint
records = [change(), observation('row', {'email':'old@example.invalid'})]
print(proof_fingerprint(ReconstructionEngine(EvidenceIndex(records)).reconstruct(request())))
"""
    hashes = []
    for seed in ("0", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed,
                   PYTHONPATH=os.pathsep.join([str(root / "code"), str(root / "code/tests")]))
        result = subprocess.run([sys.executable, "-B", "-c", script], env=env,
                                capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        hashes.append(result.stdout.strip())
    assert len(hashes[0]) == 64 and hashes[0] == hashes[1]


def test_summary_excludes_subject_payloads_and_does_not_claim_accuracy():
    index = EvidenceIndex([change(), observation("row", {"email": "old@example.invalid"})])
    bundle = SimpleNamespace(index=index, files=(), has_errors=False)
    report = reconstruction_summary(bundle, (request(),))
    encoded = json.dumps(report)
    assert "old@example.invalid" not in encoded and "subject-A" not in encoded
    assert report["output_written"] is report["audit_complete"] is False
    assert report["identity_accuracy"] == report["temporal_accuracy"] == "NOT_MEASURED"
    assert report["policy_status"] == "NOT_IMPLEMENTED"


def test_reconstruction_cli_uses_requested_dataset_and_never_writes_predictions(tmp_path, monkeypatch, capsys):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("phase_three_cli", root / "code/main.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    import ghosttrace.ingest.corpus as corpus
    index = EvidenceIndex([change(), observation("row", {"email": "old@example.invalid"})])
    def load(path):
        assert path == tmp_path
        return SimpleNamespace(index=index, files=(), has_errors=False)
    monkeypatch.setattr(corpus, "ingest_dataset", load)
    monkeypatch.setattr(cli, "load_requests", lambda path: (request(),))
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    sentinel = tmp_path / "output.csv"
    sentinel.write_text("existing prediction", encoding="utf-8")
    assert cli.main(["--reconstruct-evidence", "--dataset-root", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["phase"] == "03"
    assert sentinel.read_text(encoding="utf-8") == "existing prediction"
