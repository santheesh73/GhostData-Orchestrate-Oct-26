"""Packaging must use the independent oracle and preserve prior bundles."""
import copy
import csv
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

from fixtures.history_cases import request
from fixtures.contract_cases import expected_demo_rows

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("release_packager", ROOT / "scripts/package.py")
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


@pytest.fixture
def inputs(tmp_path, context, monkeypatch):
    rows = expected_demo_rows()
    requests = list(context[0])
    for n in range(515):
        case = f"extra-{n:04d}"
        rows.append({"case_id": case, "deletion_status": "NOT_APPLICABLE", "steps_json": []})
        requests.append(replace(request(case=case), request_text="Export my data."))
    rows.sort(key=lambda r: r["case_id"])
    monkeypatch.setattr(package, "load_requests", lambda _: requests)
    monkeypatch.setattr(package, "load_evidence_catalog", lambda _: context[2])
    def write(values):
        with (tmp_path / "output.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["case_id", "deletion_status", "steps_json"])
            writer.writerows((r["case_id"], r["deletion_status"], json.dumps(r["steps_json"])) for r in values)
    write(rows)
    return tmp_path, rows, write


def test_packaging_accepts_full_independent_contract_fixture(inputs):
    root, _, _ = inputs
    assert package.validate_output(root, root / "output.csv")[2]["contract_valid"] is True


@pytest.mark.parametrize("mutation", ["duplicate", "extra", "missing", "order", "field", "state", "number", "citation", "nondeletion"])
def test_packaging_rejects_malformed_output_instead_of_repairing(inputs, mutation):
    root, rows, write = inputs
    rows = copy.deepcopy(rows)
    complete = next(r for r in rows if r["deletion_status"] == "COMPLETE")
    if mutation == "duplicate": rows[-1] = rows[0]
    elif mutation == "extra": rows[-1]["case_id"] = "unrequested"
    elif mutation == "missing": rows.pop()
    elif mutation == "order": rows.reverse()
    elif mutation == "field": complete["steps_json"][0]["invented"] = True
    elif mutation == "state": complete["steps_json"][0]["state"] = "PRESENT"
    elif mutation == "number": complete["steps_json"][0]["step_no"] = True
    elif mutation == "citation": complete["steps_json"][0]["evidence_id"] = "unprovided"
    else: complete["deletion_status"] = "NOT_APPLICABLE"
    write(rows)
    original = (root / "output.csv").read_bytes()
    with pytest.raises(package.PackageError): package.validate_output(root, root / "output.csv")
    assert (root / "output.csv").read_bytes() == original


@pytest.mark.parametrize("name", ["../outside", "dataset/hidden.csv", "nested/code.zip", ".env", "credentials.json", "C:/absolute", "code\\bad.py"])
def test_forbidden_members_cannot_enter_code_zip(tmp_path, name):
    with pytest.raises(package.PackageError): package.safe_file(tmp_path, name)


def test_secret_member_is_rejected(tmp_path):
    (tmp_path / "bad.txt").write_text("ghp_" + "A" * 30)
    with pytest.raises(package.PackageError, match="credential"): package.safe_file(tmp_path, "bad.txt")


def test_build_records_exact_bytes_and_never_overwrites_bundle(tmp_path):
    destination = tmp_path / "new-bundle"
    validated = {"code": {"code/main.py": b"print('synthetic')"}, "artifacts": {"output.csv": b"synthetic-only"}, "proof": {"synthetic": True}}
    manifest = package.build_package(tmp_path, destination, validated)
    with zipfile.ZipFile(destination / "code.zip") as archive:
        assert archive.namelist() == ["code/main.py"]
        assert package.sha(archive.read("code/main.py")) == manifest["members"]["code/main.py"]
    original = (destination / "code.zip").read_bytes()
    with pytest.raises(package.PackageError): package.build_package(tmp_path, destination, validated)
    assert (destination / "code.zip").read_bytes() == original


def test_structural_diagnostic_cannot_build_a_bundle(tmp_path):
    validated = {"proof": {"semantic_support": "NOT_CHECKED"}}
    with pytest.raises(package.PackageError): package.build_package(tmp_path, tmp_path / "blocked", validated)
    assert not (tmp_path / "blocked").exists()
