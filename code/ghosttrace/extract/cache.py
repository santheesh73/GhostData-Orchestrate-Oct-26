"""Content-addressed atomic cache; validation is repeated on every replay."""

import hashlib
import os
from pathlib import Path
import tempfile
import re

from ..ingest.normalization import canonical_json, strict_json

MAX_CACHE_BYTES = 8 * 1024 * 1024


def cache_key(context):
    return hashlib.sha256(canonical_json(context).encode("utf-8")).hexdigest()


class ExtractionCache:
    def __init__(self, root):
        self.root = Path(root)
        self.hits = self.misses = self.rejected = 0

    def _path(self, key):
        if not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{64}", key):
            raise ValueError("invalid cache key")
        path = self.root / (key + ".json")
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise ValueError("cache entry escapes cache root")
        return path

    def read(self, key, validate):
        path = self._path(key)
        try:
            with path.open("rb") as stream:
                data = stream.read(MAX_CACHE_BYTES + 1)
            if len(data) > MAX_CACHE_BYTES:
                raise ValueError("cache size")
            entry = strict_json(data.decode("utf-8"))
            if set(entry) != {"key", "payload", "payload_sha256"} or entry["key"] != key:
                raise ValueError("cache key")
            encoded = canonical_json(entry["payload"])
            if hashlib.sha256(encoded.encode()).hexdigest() != entry["payload_sha256"]:
                raise ValueError("cache integrity")
            result = validate(entry["payload"])
            self.hits += 1
            return result
        except FileNotFoundError:
            self.misses += 1
            return None
        except (ValueError, TypeError, KeyError, OSError, UnicodeError):
            self.rejected += 1
            self.misses += 1
            return None

    def write(self, key, payload):
        destination = self._path(key)
        self.root.mkdir(parents=True, exist_ok=True)
        encoded = canonical_json(payload)
        entry = canonical_json({"key": key, "payload": payload,
                                "payload_sha256": hashlib.sha256(encoded.encode()).hexdigest()}).encode("utf-8")
        if len(entry) > MAX_CACHE_BYTES:
            raise ValueError("cache entry exceeds budget")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.root, suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(entry)
            os.replace(temporary, destination)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
