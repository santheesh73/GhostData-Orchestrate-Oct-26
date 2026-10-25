"""Optional PyMuPDF/Pillow plus local Windows OCR or Tesseract. No network."""

import hashlib
import importlib.metadata
import io
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

from ..ingest.normalization import strict_json
from .models import ExtractionError, TextUnit, Transcript

# JUDGEMENT resource bounds, not tuned to challenge labels.
MAX_PAGES = 32
MAX_PIXELS = 20_000_000
MAX_TEXT = 2_000_000
MAX_UNITS = 20_000
OCR_TIMEOUT = 45
HELPER = Path(__file__).with_name("windows_ocr.ps1")


def backend_identity():
    def version(name):
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return "unavailable"
    return {"adapter": "local-v1", "pdf": version("PyMuPDF"), "image": version("Pillow"),
            "ocr": "winrt-" + platform.version() if os.name == "nt" else "tesseract",
            "ocr_language": "en-US" if os.name == "nt" else "eng",
            "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "tesseract": shutil.which("tesseract") or "unavailable",
            "helper_sha256": hashlib.sha256(HELPER.read_bytes()).hexdigest()}


def _ocr(path, page=1):
    if os.name == "nt":
        executable = shutil.which("powershell.exe")
        if not executable:
            raise ExtractionError("LOCAL_OCR_UNAVAILABLE")
        # Fixed reviewed program text; the document path is data in an env var.
        # No execution-policy/profile change and no document text is executed.
        command = "& {\n" + HELPER.read_text(encoding="utf-8") + "\n} -Path $env:GHOSTTRACE_OCR_FILE"
        result = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-Command", command],
            env=dict(os.environ, GHOSTTRACE_OCR_FILE=str(Path(path).resolve())),
            capture_output=True, timeout=OCR_TIMEOUT, check=False)
        if result.returncode or len(result.stdout) > MAX_TEXT * 4:
            raise ExtractionError("LOCAL_OCR_FAILED")
        payload = strict_json(result.stdout.decode("utf-8-sig"))
        lines = payload.get("lines", [])
        units = []
        for index, line in enumerate(lines, 1):
            words = line.get("words", [])
            boxes = [word["bbox"] for word in words]
            bbox = ()
            if boxes:
                x, y = min(b[0] for b in boxes), min(b[1] for b in boxes)
                bbox = (x, y, max(b[0] + b[2] for b in boxes) - x, max(b[1] + b[3] for b in boxes) - y)
            units.append(TextUnit(f"page:{page}/line:{index}", line["text"], page, bbox))
        return tuple(units), "windows-ocr/" + payload["language"]
    binary = shutil.which("tesseract")
    if binary:
        result = subprocess.run([binary, str(path), "stdout", "-l", "eng", "tsv"], capture_output=True,
                                timeout=OCR_TIMEOUT, check=False)
        if result.returncode or len(result.stdout) > MAX_TEXT * 4:
            raise ExtractionError("LOCAL_OCR_FAILED")
        import csv
        from collections import defaultdict
        lines = defaultdict(list)
        for row in csv.DictReader(io.StringIO(result.stdout.decode("utf-8")), delimiter="\t"):
            if row["text"].strip():
                lines[(row["block_num"], row["par_num"], row["line_num"])].append(row["text"])
        return tuple(TextUnit(f"page:{page}/line:{i}", " ".join(words), page)
                     for i, words in enumerate(lines.values(), 1)), "tesseract"
    raise ExtractionError("LOCAL_OCR_UNAVAILABLE")


def read_document(path, data):
    """Read supplied bytes; image metadata/comments are not OCR evidence."""
    suffix = Path(path).suffix.casefold()
    units, incomplete, backend = [], [], []
    if suffix == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ExtractionError("DOCUMENT_MAGIC_MISMATCH")
        try:
            import fitz
        except ImportError as exc:
            raise ExtractionError("PDF_DEPENDENCY_UNAVAILABLE") from exc
        with fitz.open(stream=data, filetype="pdf") as document:
            if document.needs_pass or not 0 < len(document) <= MAX_PAGES:
                raise ExtractionError("UNSUPPORTED_PDF_PAGES_OR_ENCRYPTION")
            pages = len(document)
            backend.append("pymupdf")
            for number, page in enumerate(document, 1):
                page_units = []
                for index, block in enumerate(page.get_text("blocks"), 1):
                    if len(block) >= 7 and block[6] == 0 and block[4].strip():
                        page_units.append(TextUnit(f"page:{number}/block:{index}", block[4], number,
                                                   (block[0], block[1], block[2] - block[0], block[3] - block[1])))
                if not page_units:
                    if page.rect.width * page.rect.height * 4 > MAX_PIXELS:
                        raise ExtractionError("PDF_RENDER_BUDGET_EXCEEDED")
                    with tempfile.TemporaryDirectory(prefix="ghosttrace-ocr-") as folder:
                        rendered = Path(folder) / "page.png"
                        page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(rendered)
                        try:
                            page_units, method = _ocr(rendered, number)
                            backend.append(method)
                        except ExtractionError:
                            incomplete.append(number)
                if not page_units:
                    incomplete.append(number)
                units.extend(page_units)
    else:
        if not ((suffix == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n")) or
                (suffix in {".jpg", ".jpeg"} and data.startswith(b"\xff\xd8\xff"))):
            raise ExtractionError("DOCUMENT_MAGIC_MISMATCH")
        try:
            from PIL import Image
        except ImportError as exc:
            raise ExtractionError("IMAGE_DEPENDENCY_UNAVAILABLE") from exc
        with Image.open(io.BytesIO(data)) as image:
            if image.width * image.height > MAX_PIXELS:
                raise ExtractionError("IMAGE_PIXEL_BUDGET_EXCEEDED")
            image.verify()
        # Read the same bounded bytes, avoiding a source-file race during OCR.
        with tempfile.TemporaryDirectory(prefix="ghosttrace-ocr-") as folder:
            snapshot = Path(folder) / ("input" + suffix)
            snapshot.write_bytes(data)
            extracted, method = _ocr(snapshot)
            units.extend(extracted)
            backend.append(method)
        pages = 1
        if not units:
            incomplete.append(1)
    if len(units) > MAX_UNITS or sum(len(u.text) for u in units) > MAX_TEXT:
        raise ExtractionError("DOCUMENT_TEXT_BUDGET_EXCEEDED")
    if not units:
        raise ExtractionError("NO_READABLE_DOCUMENT_TEXT")
    return Transcript("+".join(sorted(set(backend))), "local-v1", pages, tuple(units), tuple(sorted(set(incomplete))))
