#!/usr/bin/env python3
"""Validate source-grounded predictions and atomically build a NEW local bundle."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from ghosttrace.ingest.loader import load_requests, load_evidence_catalog
from ghosttrace.quality.validator import read_output, validate_rows, OutputError

class PackageError(ValueError):
    pass

def sha(data):
    return hashlib.sha256(data).hexdigest()

def safe_file(root, name):
    path = PurePosixPath(name)
    forbidden = {"dataset", ".git", ".agents", ".ghosttrace", "__pycache__", "venv", ".venv", "node_modules"}
    if (not name or path.as_posix() != name or "\\" in name or path.is_absolute() or ":" in name or any(ord(c) < 32 for c in name)
            or any(p in {"", ".", ".."} or p.casefold() in forbidden for p in path.parts)):
        raise PackageError("unsafe archive member: " + name)
    source = root.joinpath(*path.parts)
    if source.suffix.casefold() in {".zip", ".tar", ".gz", ".7z", ".pem", ".key", ".pyc", ".pyo", ".db"} or source.name.startswith(".env") or source.name.casefold() in {"auth.json", "config.toml", "credentials.json"}:
        raise PackageError("forbidden archive member: " + name)
    if not source.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in (source, *source.parents)):
        raise PackageError("linked or escaping member: " + name)
    if not source.is_file() or source.stat().st_size == 0:
        raise PackageError("missing or empty member: " + name)
    content = source.read_bytes()
    if re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:sk-proj-|ghp_)[A-Za-z0-9_-]{20,}", content):
        raise PackageError("possible credential in member: " + name)
    return content

def validate_output(root, output, *, prediction_mode=False):
    requests = load_requests(root / "dataset/deletion_requests.csv")
    if len(requests) != 518:
        raise PackageError("official run requires exactly 518 input requests")
    rows = read_output(output)
    report = validate_rows(rows, requests, load_evidence_catalog(root / "dataset"), allow_empty_complete=prediction_mode)
    if not report.valid:
        raise PackageError("output contract failed: " + json.dumps(report.as_dict()))
    return requests, rows, report.as_dict()

def semantic_check(root, requests, rows, *, prediction_mode=False):
    from evaluation.audit_evaluation import run_audits, audit_fingerprint, corpus_fingerprint, implementation_fingerprint
    from ghosttrace.quality.audit_gate import check_audit
    from ghosttrace.emit.operation_mapper import emit_decision
    bundle, engine, audits, timing, extractor = run_audits(root / "dataset", requests,
        with_extraction=True, cache_dir=root / ".ghosttrace/packaging", prediction_defaults=prediction_mode)
    blocked = {a.decision.request.case_id: list(check_audit(a, engine.observations)) for a in audits if check_audit(a, engine.observations)}
    if blocked and not prediction_mode:
        raise PackageError("semantic gate blocked " + str(len(blocked)) + " cases: " + json.dumps(blocked, sort_keys=True))
    expected = [emit_decision(a.decision, allow_uncertainty=prediction_mode).as_dict() for a in audits]
    if rows != expected:
        raise PackageError("output does not match this source's independently gated audit run")
    return {"prediction_mode": prediction_mode, "proof_diagnostic_cases": len(blocked),
            "semantic_certification": "NOT_CLAIMED" if prediction_mode else "CHECKED",
            "audit_sha256": audit_fingerprint(audits), "corpus_sha256": corpus_fingerprint(bundle),
            "implementation_sha256": implementation_fingerprint(), "timing": timing,
            "usage": extractor.runner.ledger.summary()}

def member_snapshot(root, contract):
    if type(contract) is not dict or set(contract) != {"code_files"} or type(contract["code_files"]) is not list or not contract["code_files"]:
        raise PackageError("invalid explicit release-files contract")
    names = contract["code_files"]
    if any(type(n) is not str for n in names) or len({n.casefold() for n in names}) != len(names):
        raise PackageError("duplicate or invalid archive members")
    required = {"code/main.py", "README.md", "code/evaluation/evaluation_report.md", "code/evaluation/usage_report.md"}
    if not required <= set(names):
        raise PackageError("required code/report files not in contract")
    data = {n: safe_file(root, n) for n in sorted(names)}
    # Official archive report paths; these bytes are the same canonical reports.
    for name in ("evaluation_report.md", "usage_report.md"):
        data["evaluation/" + name] = data["code/evaluation/" + name]
    return data

def validate_submission_files(root=ROOT, *, semantic=True, prediction_mode=False):
    requests, rows, validation = validate_output(root, root / "output.csv", prediction_mode=prediction_mode)
    code = member_snapshot(root, json.loads((root / "release-files.json").read_text(encoding="utf-8")))
    artifacts = {name: safe_file(root, name) for name in ("README.md", "log.txt")}
    artifacts["output.csv"] = (root / "output.csv").read_bytes()
    proof = semantic_check(root, requests, rows, prediction_mode=prediction_mode) if semantic else {"semantic_support": "NOT_CHECKED"}
    if not semantic:
        return {"contract": validation, "proof": proof}
    for name, content in code.items():
        source = "code/" + name if name.startswith("evaluation/") else name
        if safe_file(root, source) != content:
            raise PackageError("source changed during semantic validation: " + source)
    if (root / "output.csv").read_bytes() != artifacts["output.csv"]:
        raise PackageError("output changed during semantic validation")
    return {"contract": validation, "proof": proof, "code": code, "artifacts": artifacts}

def build_package(root, destination, validated):
    destination = destination.resolve()
    if destination.exists() or not destination.parent.is_dir():
        raise PackageError("bundle destination must be new with an existing parent")
    if not destination.is_relative_to(root.resolve()) or any(p in {"dataset", "code", ".git"} for p in destination.relative_to(root.resolve()).parts):
        raise PackageError("bundle destination must be inside the repository and outside input directories")
    if "semantic_support" in validated["proof"]:
        raise PackageError("structural-only diagnostics cannot build a bundle")
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    # Bytes/hashes identify exact sources, including any uncommitted edits. Git
    # HEAD is context, never a claim that dirty files equal that commit.
    manifest = {"source_commit_context": commit, "proof": validated["proof"],
        "members": {n: sha(b) for n, b in validated["code"].items()},
        "artifacts": {n: sha(b) for n, b in validated["artifacts"].items()}, "readiness": "LOCAL_CHECKS_PASSED"}
    with tempfile.TemporaryDirectory(prefix="ghosttrace-package-", dir=destination.parent) as temp:
        stage = Path(temp) / "bundle"
        stage.mkdir()
        with zipfile.ZipFile(stage / "code.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in validated["code"].items():
                archive.writestr(name, content)
        with zipfile.ZipFile(stage / "code.zip") as archive:
            if archive.testzip() is not None or set(archive.namelist()) != set(validated["code"]):
                raise PackageError("archive integrity or inventory mismatch")
            for name, digest in manifest["members"].items():
                if sha(archive.read(name)) != digest:
                    raise PackageError("archive member hash mismatch")
        for name, content in validated["artifacts"].items():
            (stage / name).write_bytes(content)
        manifest["code_zip_sha256"] = sha((stage / "code.zip").read_bytes())
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        stage.rename(destination)
    return manifest

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--prediction-mode", action="store_true", help="package explicitly requested heuristic predictions; retain proof diagnostics")
    parser.add_argument("--structural-only", action="store_true", help="diagnostic only; never builds")
    parser.add_argument("--out", type=Path, default=ROOT / "submission-verified")
    args = parser.parse_args(argv)
    try:
        validated = validate_submission_files(semantic=not args.structural_only, prediction_mode=args.prediction_mode)
        if args.check_only or args.structural_only:
            print(json.dumps({"contract": validated["contract"], "proof": validated["proof"], "package_built": False}))
        else:
            manifest = build_package(ROOT, args.out, validated)
            print(json.dumps({"result": "PACKAGE BUILT", "path": str(args.out), "manifest": manifest}))
        return 0
    except (PackageError, OutputError, ValueError, OSError) as exc:
        print(json.dumps({"result": "PACKAGE BLOCKED", "reason": str(exc), "package_built": False}))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
