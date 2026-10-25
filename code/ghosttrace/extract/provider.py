"""Optional OpenAI Responses adapter. No credentials, model or prices in code."""

import base64
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

from ..ingest.normalization import strict_json
from .cache import cache_key
from .models import ExtractionError, ModelReply


class ProviderError(ExtractionError):
    def __init__(self, code, retryable=False):
        super().__init__(code)
        self.retryable = retryable


def _object(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


STRING = {"type": "string"}
FIELD_SCHEMA = _object({k: STRING for k in ("name", "value_json", "quote", "locator")})
RECORD_SCHEMA = _object({**{k: STRING for k in ("resource_id", "system_id", "category", "quote", "locator")},
                         "fields": {"type": "array", "items": FIELD_SCHEMA}})
SCHEMAS = {
    "document": _object({"records": {"type": "array", "items": RECORD_SCHEMA},
                         "uncertainties": {"type": "array", "items": STRING}}),
    "intent": _object({"authorization": {"type": "string", "enum": ["DELETION", "NON_DELETION", "UNRESOLVED"]},
                       "language": STRING, "english_translation": STRING, "quote": STRING}),
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OpenAIProvider:
    def __init__(self, model=None, api_key=None, transport=None):
        self.model = model or os.environ.get("GHOSTTRACE_MODEL", "")
        self._key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.model:
            raise ProviderError("MODEL_NOT_CONFIGURED")
        self.configured = bool(self._key)
        self.identity = {"provider": "openai", "model": self.model, "adapter": "responses-v1", "max_output_tokens": 2048}
        self.transport = transport or urllib.request.build_opener(NoRedirect()).open

    def complete(self, task, prompt, content, image=None):
        if not self.configured:
            raise ProviderError("MODEL_NOT_CONFIGURED")
        parts = [{"type": "input_text", "text": json.dumps(content, ensure_ascii=False)}]
        if image is not None:
            parts.append({"type": "input_image", "image_url": "data:image/png;base64," + base64.b64encode(image).decode(), "detail": "high"})
        body = {"model": self.model, "store": False, "max_output_tokens": 2048,
                "instructions": prompt, "input": [{"role": "user", "content": parts}],
                "text": {"format": {"type": "json_schema", "name": "ghosttrace_" + task,
                                      "strict": True, "schema": SCHEMAS[task]}}}
        request = urllib.request.Request("https://api.openai.com/v1/responses", method="POST",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + self._key, "Content-Type": "application/json"})
        try:
            with self.transport(request, timeout=30) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024:
                raise ProviderError("PROVIDER_RESPONSE_TOO_LARGE")
            data = strict_json(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ProviderError("PROVIDER_HTTP_" + str(exc.code), exc.code == 429 or exc.code >= 500) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProviderError("PROVIDER_TRANSPORT_ERROR", True) from None
        except (ValueError, UnicodeError):
            raise ProviderError("PROVIDER_INVALID_ENVELOPE") from None
        if not isinstance(data, dict) or not isinstance(data.get("output"), list):
            raise ProviderError("PROVIDER_INVALID_ENVELOPE")
        output, refused = [], False
        for item in data.get("output", []):
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            parts = item.get("content")
            for part in parts if isinstance(parts, list) else []:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    output.append(part["text"])
                refused |= part.get("type") == "refusal"
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        def count(key):
            value = usage.get(key)
            return value if type(value) is int and value >= 0 else None
        details = usage.get("input_tokens_details")
        cached = details.get("cached_tokens") if isinstance(details, dict) else None
        if type(cached) is not int or count("input_tokens") is None or not 0 <= cached <= count("input_tokens"):
            cached = None
        reported_model = data.get("model")
        return ModelReply("\n".join(output) if data.get("status") == "completed" else "",
                          reported_model if isinstance(reported_model, str) else self.model,
                          count("input_tokens"), count("output_tokens"), cached, refused)


class ModelRunner:
    def __init__(self, provider, cache, ledger, max_calls=0, attempts=3):
        if type(max_calls) is not int or not 0 <= max_calls <= 64 or type(attempts) is not int or not 1 <= attempts <= 3:
            raise ValueError("model call/attempt budget outside supported bounds")
        self.provider, self.cache, self.ledger = provider, cache, ledger
        self.max_calls, self.attempts = max_calls, attempts
        self.diagnostics = []

    def run(self, task, context, content, validate, image=None):
        if self.provider is None:
            self.diagnostics.append("MODEL_NOT_CONFIGURED")
            return None
        prompt = (Path(__file__).parent / "prompts" / (task + ".txt")).read_text(encoding="utf-8")
        key = cache_key({"task": task, "cache_schema": 2, "context": context, "content": content,
                         "image_sha256": hashlib.sha256(image).hexdigest() if image is not None else None,
                         "provider": self.provider.identity, "prompt": prompt, "schema": SCHEMAS[task]})
        def cached(entry):
            if not isinstance(entry, dict) or set(entry) != {"data", "usage"}:
                raise ExtractionError("INVALID_MODEL_CACHE")
            result = validate(entry["data"])
            history = entry["usage"]
            if not isinstance(history, list) or not 1 <= len(history) <= 3:
                raise ExtractionError("INVALID_USAGE_CACHE")
            for usage in history:
                if not isinstance(usage, dict) or set(usage) != {"provider", "model", "outcome", "input_tokens", "output_tokens", "cached_input_tokens"}:
                    raise ExtractionError("INVALID_USAGE_CACHE")
                if any(not isinstance(usage[k], str) for k in ("provider", "model", "outcome")):
                    raise ExtractionError("INVALID_USAGE_CACHE")
                for name in ("input_tokens", "output_tokens", "cached_input_tokens"):
                    if usage[name] is not None and (type(usage[name]) is not int or usage[name] < 0):
                        raise ExtractionError("INVALID_USAGE_CACHE")
                if usage["cached_input_tokens"] is not None and usage["input_tokens"] is not None and usage["cached_input_tokens"] > usage["input_tokens"]:
                    raise ExtractionError("INVALID_USAGE_CACHE")
            self.ledger.build_usage[key] = history
            return result
        result = self.cache.read(key, cached)
        if result is not None:
            self.ledger.cache_hits += 1
            return result
        if not getattr(self.provider, "configured", True):
            self.diagnostics.append("MODEL_NOT_CONFIGURED")
            return None
        if len(json.dumps(content, ensure_ascii=False)) > 128000:
            self.diagnostics.append("MODEL_INPUT_BUDGET_EXCEEDED")
            return None
        job_start = len(self.ledger.calls)
        for _ in range(self.attempts):
            if len(self.ledger.calls) >= self.max_calls:
                self.ledger.budget_skips += 1
                self.diagnostics.append("MODEL_CALL_BUDGET_EXHAUSTED")
                break
            reply = None
            try:
                reply = self.provider.complete(task, prompt, content, image)
                if reply.refused:
                    self.ledger.record(self.provider.identity["provider"], reply.model, reply, "REFUSED")
                    self.diagnostics.append("MODEL_REFUSED")
                    break
                result = validate(strict_json(reply.text))
                self.ledger.record(self.provider.identity["provider"], reply.model, reply, "VALID")
                try:
                    self.cache.write(key, {"data": result, "usage": self.ledger.calls[job_start:]})
                except (OSError, ValueError):
                    self.diagnostics.append("MODEL_CACHE_WRITE_FAILED")
                return result
            except ProviderError as exc:
                self.ledger.record(self.provider.identity["provider"], self.provider.identity["model"], reply)
                self.diagnostics.append(str(exc))
                if not exc.retryable:
                    break
            except (ValueError, TypeError, KeyError):
                self.ledger.record(self.provider.identity["provider"], reply.model if reply else self.provider.identity["model"], reply, "INVALID")
                self.diagnostics.append("MODEL_OUTPUT_REJECTED")
        return None
