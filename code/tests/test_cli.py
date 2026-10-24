import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run_cli(*args, cwd=None):
    return subprocess.run([sys.executable, "-B", str(ROOT / "code/main.py"), *args],
                          cwd=cwd, capture_output=True, text=True, check=False)


def test_real_input_diagnostics_work_from_another_directory(tmp_path):
    result = run_cli("--validate-inputs-only", cwd=tmp_path)
    assert result.returncode == 0
    assert json.loads(result.stdout)["requests"] == 518
    assert json.loads(result.stdout)["output_written"] is False


def test_default_runner_returns_unresolved_without_touching_predictions(tmp_path):
    output = ROOT / "output.csv"
    before = output.read_bytes() if output.exists() else None
    result = run_cli(cwd=tmp_path)
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["unresolved_count"] == report["request_count"] == 518
    assert len(report["unresolved_case_ids"]) == 518
    assert (output.read_bytes() if output.exists() else None) == before


def test_demo_cannot_overwrite_dataset_or_final_output():
    for path in (ROOT / "dataset/sample_output.csv", ROOT / "output.csv"):
        result = run_cli("--demo", "--output", str(path))
        assert result.returncode == 2


def test_synthetic_demo_cli_in_isolated_root(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("phase_one_cli", ROOT / "code/main.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    sentinel = tmp_path / "output.csv"
    sentinel.write_text("untouched", encoding="utf-8")
    assert cli.main(["--demo"]) == 0
    assert json.loads(capsys.readouterr().out)["synthetic"] is True
    assert (tmp_path / ".ghosttrace/phase01-demo.csv").exists()
    assert sentinel.read_text(encoding="utf-8") == "untouched"


def test_sample_contract_inspector():
    result = subprocess.run([sys.executable, "-B", str(ROOT / "code/evaluation/main.py"),
                             "--inspect-samples"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["rows"] == 32 and report["steps"] == 193
    assert report["validation"]["contract_valid"]
    assert report["prediction_accuracy"] == "NOT_MEASURED"


def test_runtime_does_not_import_public_label_utilities():
    for relative in ["code/main.py", "code/ghosttrace/pipeline.py", "code/ghosttrace/demo.py"]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        tree = ast.parse(text)
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not any(name.startswith("evaluation") or "contract_mining" in name for name in imports)
        assert "sample_output.csv" not in text


def test_comparator_cli_accepts_synthetic_context_and_detects_mutation(tmp_path, context):
    import csv
    from fixtures.contract_cases import expected_demo_rows
    from ghosttrace.pipeline import publish_decisions
    from ghosttrace.spec_registry import REQUEST_COLUMNS

    requests, decisions, catalog = context
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    request_path, reference, candidate = (tmp_path / name for name in ("requests.csv", "reference.csv", "candidate.csv"))
    with request_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(REQUEST_COLUMNS)
        for request in requests:
            writer.writerow([request.case_id, request.email, request.requested_at.isoformat(),
                             request.reported_status, request.reported_at.isoformat(),
                             request.audit_at.isoformat(), request.request_text])
    with reference.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        for row in expected_demo_rows():
            writer.writerow([row["case_id"], row["deletion_status"], json.dumps(row["steps_json"])])
    for name, header, data in [
        ("evidence_files.csv", ["file_id", "captured_at"],
         [["synthetic_evidence", requests[0].audit_at.isoformat()]]),
        ("system_activity.csv", ["activity_id", "event_time"], []),
        ("user_audit_log.csv", ["audit_id", "event_time"], []),
    ]:
        with (dataset / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(data)
    publish_decisions(decisions, requests, catalog, candidate)
    command = [sys.executable, "-B", str(ROOT / "code/evaluation/main.py"), "--predictions", str(candidate),
               "--expected", str(reference), "--requests", str(request_path), "--dataset-root", str(dataset)]
    valid = subprocess.run(command, capture_output=True, text=True)
    assert valid.returncode == 0, valid.stderr
    assert json.loads(valid.stdout)["exact_rows"] == 3
    candidate.write_text(candidate.read_text(encoding="utf-8").replace(
        "synthetic_complete,COMPLETE,", "synthetic_complete,UNKNOWN,"), encoding="utf-8")
    broken = subprocess.run(command, capture_output=True, text=True)
    assert broken.returncode == 1, broken.stderr
    report = json.loads(broken.stdout)
    assert not report["candidate_validation"]["contract_valid"]
    assert report["status_correct"] == 2
