"""Selective extraction and provenance-preserving integration with Stage 1."""

from collections import Counter
from dataclasses import replace
import hashlib
import os
import re
from pathlib import Path
import subprocess

from ..ingest.corpus import IngestionBundle
from ..ingest.evidence_index import EvidenceIndex
from ..ingest.normalization import MAX_FILE_BYTES, ParseDiagnostic, ParseResult, ParseStatus, canonical_json, make_observation, strict_json
from ..ingest.structured_parser import evidence_path
from ..models import Authorization
from ..policy.applicability import classify_request
from ..policy.models import Intent
from .cache import cache_key
from .documents import CATEGORIES, SYSTEMS, local_records
from .local import backend_identity, read_document
from .models import ExtractionError
from .validation import validate_intent, validate_records, validate_transcript


class SelectiveExtractor:
    def __init__(self, cache, runner, reader=read_document):
        self.cache, self.runner, self.reader = cache, runner, reader
        self.files, self.intents = [], []
        self.backend = backend_identity()

    def source(self, root, previous):
        source, format_name = previous.source, previous.format
        digest = previous.source_sha256
        try:
            with evidence_path(root, source.path).open("rb") as stream:
                data = stream.read(MAX_FILE_BYTES + 1)
            if len(data) > MAX_FILE_BYTES:
                raise ExtractionError("SOURCE_SIZE_EXCEEDED")
            digest = hashlib.sha256(data).hexdigest()
            if digest != previous.source_sha256:
                raise ExtractionError("SOURCE_CHANGED_DURING_EXTRACTION")
            context = {"file_id": source.evidence_id, "path": source.path, "origin": source.source_kind,
                       "captured_at": source.available_at.isoformat() if source.available_at else None,
                       "source_sha256": digest, "adapter": "extraction-v1", "backend": self.backend}
            key = cache_key(context)
            transcript = self.cache.read(key, validate_transcript)
            cached = transcript is not None
            if transcript is None:
                transcript = validate_transcript(self.reader(evidence_path(root, source.path), data).as_dict())
                try:
                    self.cache.write(key, transcript.as_dict())
                except (OSError, ValueError):
                    self.runner.diagnostics.append("LOCAL_CACHE_WRITE_FAILED")
            system, category = SYSTEMS.get(source.source_kind, ""), CATEGORIES.get(source.source_kind, "")
            records = local_records(transcript, system, category)
            # Raw capture is complete only as text. Semantic work is selective
            # and bounded; it is never a mandatory call on every request.
            if not records["records"] or not category:
                content = {"expected_system": system, "expected_category": category,
                           "units": [{"locator": u.locator, "text": u.text} for u in transcript.units]}
                modeled = self.runner.run("document", context, content,
                    lambda value: validate_records(value, transcript, system, category),
                    image=data if format_name == "png" else None)
                if modeled is not None:
                    records = modeled
            observations = []
            for unit in transcript.units:
                observations.append(make_observation(source, digest, unit.locator,
                    {"text": unit.text, "page": unit.page, "bbox": unit.bbox,
                     "extractor": transcript.backend, "extractor_version": transcript.version},
                    observed_at=source.available_at, time_basis="document_capture", claim_kind="DOCUMENT_TEXT"))
            for number, record in enumerate(records["records"], 1):
                facts = {f["name"]: strict_json(f["value_json"]) for f in record["fields"]}
                if "record_type" in facts and facts["record_type"] != category:
                    raise ExtractionError("CONFLICTING_DOCUMENT_CATEGORY")
                payload = {**facts, "resource_id": record["resource_id"], "extraction_proof": record,
                           "extractor": transcript.backend, "extraction_schema": "v1"}
                observations.append(make_observation(source, digest, f"document/record:{number}", payload,
                    system=system, resource=record["resource_id"], category=category,
                    physical_copy="document:" + source.evidence_id, observed_at=source.available_at, time_basis="document_capture"))
            diagnostics = tuple(ParseDiagnostic("UNREADABLE_PAGE", f"page:{n}", "page remains unreadable", "ERROR")
                                for n in transcript.incomplete_pages)
            status = ParseStatus.PARTIAL if diagnostics else ParseStatus.PARSED
            self.files.append({"source_id": source.evidence_id, "status": status.value, "backend": transcript.backend,
                               "pages": transcript.pages, "units": len(transcript.units), "records": len(records["records"]),
                               "semantic_coverage": "PARTIAL" if records["records"] else "NOT_ESTABLISHED",
                               "cache_hit": cached, "source_sha256": digest})
            return ParseResult(source, format_name, status, digest, tuple(observations), diagnostics,
                               transcript.pages, transcript.pages - len(transcript.incomplete_pages))
        except (ValueError, TypeError, KeyError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
            code = str(exc) if isinstance(exc, ExtractionError) else "EXTRACTION_FAILED_" + type(exc).__name__
            self.files.append({"source_id": source.evidence_id, "status": "FAILED", "code": code})
            return ParseResult(source, format_name, ParseStatus.FAILED, digest, diagnostics=(
                ParseDiagnostic(code, "file", "document extraction did not establish readable source facts", "ERROR"),))

    def enrich(self, bundle, root):
        files = tuple(self.source(root, result) if result.status == ParseStatus.DEFERRED and
                      result.format in {"pdf", "png", "jpg", "jpeg"} else result for result in bundle.files)
        observations = [o for result in (*files, *bundle.context) for o in result.observations]
        return IngestionBundle(files, bundle.context, EvidenceIndex(observations), bundle.diagnostics)

    def resolve_intent(self, request, native):
        if native.authorization != Authorization.UNRESOLVED or native.reason not in {
                "UNSUPPORTED_REQUEST_LANGUAGE", "INTENT_NOT_ESTABLISHED", "UNSCOPED_DELETION_MENTION"}:
            return native
        # Non-Latin native classification stops at language detection. Repeat
        # the command/quotation guard here so that route cannot bypass it.
        if re.search(r'[`"“”]|\b(ignore (?:all |previous |prior )?instructions|system prompt|hypothetical|what happens if|if i|how (?:can|do) i)\b', request.request_text, re.IGNORECASE):
            self.intents.append({"case_id": request.case_id, "status": "AMBIGUOUS_OR_EMBEDDED_REQUEST"})
            return native
        if len(request.request_text) > 16000:
            self.intents.append({"case_id": request.case_id, "status": "INPUT_TOO_LARGE"})
            return native
        digest = hashlib.sha256(request.request_text.encode("utf-8")).hexdigest()
        result = self.runner.run("intent", {"text_sha256": digest, "adapter": "intent-v1"},
                                 {"request_text": request.request_text},
                                 lambda value: validate_intent(value, request.request_text))
        self.intents.append({"case_id": request.case_id, "status": "EXTRACTED" if result is not None else "UNRESOLVED",
                             "text_sha256": digest})
        return Intent(Authorization(result["authorization"]), "MODEL_TRANSLATED_REQUEST") if result is not None else native

    def summary(self):
        return {"phase": "05", "files": self.files, "document_status_counts": dict(Counter(f["status"] for f in self.files)),
                "text_units": sum(f.get("units", 0) for f in self.files),
                "record_observations": sum(f.get("records", 0) for f in self.files),
                "intent_tasks": self.intents, "model_diagnostics": dict(sorted(Counter(self.runner.diagnostics).items())),
                "cache": {"hits": self.cache.hits, "misses": self.cache.misses, "rejected": self.cache.rejected},
                "usage": self.runner.ledger.summary(), "audit_complete": False,
                "evidence_recall": "NOT_MEASURED", "deletion_accuracy": "NOT_MEASURED", "output_written": False}


def configured_extractor(cache_root, max_calls=0):
    from .cache import ExtractionCache
    from .provider import ModelRunner, OpenAIProvider
    from .usage import UsageLedger
    cache = ExtractionCache(cache_root)
    ledger = UsageLedger(os.environ.get("GHOSTTRACE_INPUT_USD_PER_MILLION"),
                         os.environ.get("GHOSTTRACE_OUTPUT_USD_PER_MILLION"),
                         os.environ.get("GHOSTTRACE_CACHED_INPUT_USD_PER_MILLION"))
    provider = OpenAIProvider() if os.environ.get("GHOSTTRACE_MODEL") else None
    return SelectiveExtractor(cache, ModelRunner(provider, cache, ledger, max_calls=max_calls))
