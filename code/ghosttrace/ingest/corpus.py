"""Parse once, index, and account for every manifest/context source."""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .evidence_index import EvidenceIndex
from .normalization import ParseDiagnostic, ParseResult, ParseStatus
from .structured_parser import load_context_sources, load_manifest, parse_source


@dataclass(frozen=True, slots=True)
class IngestionBundle:
    files: tuple[ParseResult, ...]
    context: tuple[ParseResult, ...]
    index: EvidenceIndex
    diagnostics: tuple[ParseDiagnostic, ...] = ()

    @property
    def has_errors(self):
        return bool(self.diagnostics) or any(r.status in {ParseStatus.FAILED, ParseStatus.PARTIAL, ParseStatus.EMPTY}
                   or (r.status == ParseStatus.DEFERRED and r.format not in {"pdf", "png", "jpg", "jpeg"})
                   for r in (*self.files, *self.context))

    def summary(self):
        def record(result):
            return {"source_id": result.source.evidence_id, "path": result.source.path,
                    "format": result.format, "status": result.status.value,
                    "source_sha256": result.source_sha256,
                    "observations": len(result.observations), "units_seen": result.units_seen,
                    "units_parsed": result.units_parsed,
                    "diagnostics": [{"code": d.code, "location": d.location,
                                     "detail": d.detail, "severity": d.severity} for d in result.diagnostics]}
        return {"phase": "02", "manifest_files": len(self.files),
                "manifest_status_counts": dict(sorted(Counter(r.status.value for r in self.files).items())),
                "context_sources": len(self.context), "indexed_observations": len(self.index),
                "has_ingestion_errors": self.has_errors, "audit_complete": False,
                "semantic_support": "NOT_CHECKED", "output_written": False,
                "corpus_diagnostics": [{"code": d.code, "location": d.location, "detail": d.detail}
                                       for d in self.diagnostics],
                "files": [record(r) for r in self.files], "context": [record(r) for r in self.context]}


def ingest_dataset(dataset_root: Path) -> IngestionBundle:
    dataset_root = Path(dataset_root)
    sources = load_manifest(dataset_root)
    files = tuple(parse_source(dataset_root, source) for source in sources)
    context = load_context_sources(dataset_root)
    observations = tuple(observation for result in (*files, *context) for observation in result.observations)
    owners = {source.evidence_id: source.path for source in sources}
    diagnostics = []
    for observation in observations:
        source = observation.evidence
        if source.citeable:
            if source.evidence_id in owners and owners[source.evidence_id] != source.path:
                diagnostics.append(ParseDiagnostic("EVIDENCE_ID_COLLISION", source.path,
                                                   "one permitted evidence ID occurs in different sources", "ERROR"))
            owners[source.evidence_id] = source.path
    return IngestionBundle(files, context, EvidenceIndex(observations), tuple(diagnostics))
