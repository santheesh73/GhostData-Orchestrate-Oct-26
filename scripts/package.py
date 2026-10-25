#!/usr/bin/env python3
"""Package the Ghost Data Still Exists submission bundle according to AGENTS.md §6.9."""

import csv
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"

SKIP_NAMES = {
    ".git", ".venv", "venv", "__pycache__", "dataset", ".pytest_cache",
    "submission", "node_modules", ".agents", "scratch", ".ghosttrace",
    ".idea", ".vscode"
}
SKIP_EXTS = {".pyc", ".pyo", ".pyd"}

def validate_submission_files():
    print("=== Validating Submission Files ===")
    
    # 1. Check output.csv
    out_csv = ROOT / "output.csv"
    assert out_csv.exists(), "output.csv does not exist at root"
    with open(out_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["case_id", "deletion_status", "steps_json"], f"Invalid header: {header}"
        rows = list(reader)
        assert len(rows) == 518, f"Expected 518 rows, got {len(rows)}"
        case_ids = [r[0] for r in rows]
        assert case_ids == sorted(case_ids), "output.csv rows must be sorted by case_id"
        for r in rows:
            assert r[1] in {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}, f"Invalid status: {r[1]}"
            steps = json.loads(r[2])
            assert isinstance(steps, list), "steps_json must be a JSON array"
    print(f"PASS: output.csv is valid (518 sorted cases, exact columns)")

    # 2. Check evaluation reports
    eval_rep = ROOT / "evaluation" / "evaluation_report.md"
    usage_rep = ROOT / "evaluation" / "usage_report.md"
    assert eval_rep.exists(), "evaluation/evaluation_report.md missing"
    assert usage_rep.exists(), "evaluation/usage_report.md missing"
    print("PASS: evaluation reports exist")

    # 3. Check README.md and log.txt
    readme = ROOT / "README.md"
    log = ROOT / "log.txt"
    assert readme.exists(), "README.md missing"
    assert log.exists(), "log.txt missing"
    print("PASS: README.md and log.txt exist")

def build_package():
    SUBMISSION.mkdir(exist_ok=True)
    
    # Copy root output.csv to submission/
    shutil.copy2(ROOT / "output.csv", SUBMISSION / "output.csv")
    shutil.copy2(ROOT / "README.md", SUBMISSION / "README.md")
    shutil.copy2(ROOT / "log.txt", SUBMISSION / "log.txt")
    
    # Copy evaluation folder
    sub_eval = SUBMISSION / "evaluation"
    sub_eval.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "evaluation" / "evaluation_report.md", sub_eval / "evaluation_report.md")
    shutil.copy2(ROOT / "evaluation" / "usage_report.md", sub_eval / "usage_report.md")

    # Build code.zip
    zip_path = SUBMISSION / "code.zip"
    included_files = []
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add code/
        for p in (ROOT / "code").rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_NAMES for part in p.parts):
                continue
            if p.suffix in SKIP_EXTS:
                continue
            rel = p.relative_to(ROOT)
            zf.write(p, rel.as_posix())
            included_files.append(rel.as_posix())
            
        # Add evaluation/
        for p in (ROOT / "evaluation").rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT)
            zf.write(p, rel.as_posix())
            included_files.append(rel.as_posix())
            
        # Add top-level docs required
        for doc in ["README.md", "DECISIONS.md", "problem_statement.md", "AGENTS.md"]:
            p = ROOT / doc
            if p.exists():
                zf.write(p, doc)
                included_files.append(doc)

    print(f"\nBuilt {zip_path} ({zip_path.stat().st_size} bytes)")
    print(f"Total files in code.zip: {len(included_files)}")
    print("\nSubmission folder contents:")
    for item in sorted(SUBMISSION.rglob("*")):
        if item.is_file():
            print(f"  {item.relative_to(SUBMISSION)} ({item.stat().st_size} bytes)")

if __name__ == "__main__":
    validate_submission_files()
    build_package()
    print("\nALL CHECKS PASSED: READY FOR SUBMISSION!")
