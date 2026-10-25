"""Actual call accounting. Unknown tokens/pricing never silently become zero."""

from decimal import Decimal, DecimalException


class UsageLedger:
    def __init__(self, input_rate=None, output_rate=None, cached_rate=None):
        try:
            self.rates = tuple(Decimal(str(v)) if v is not None else None for v in (input_rate, output_rate, cached_rate))
        except DecimalException:
            raise ValueError("invalid token rates") from None
        if any(v is not None and (not v.is_finite() or v < 0) for v in self.rates):
            raise ValueError("token rates must be finite non-negative USD per million")
        self.calls = []
        self.build_usage = {}
        self.cache_hits = 0
        self.budget_skips = 0

    def record(self, provider, model, reply=None, outcome="ERROR"):
        self.calls.append({"provider": provider, "model": model, "outcome": outcome,
            "input_tokens": reply.input_tokens if reply else None,
            "output_tokens": reply.output_tokens if reply else None,
            "cached_input_tokens": reply.cached_input_tokens if reply else None})

    def _cost(self, rows):
        if not rows:
            return "0"
        if any(r["input_tokens"] is None or r["output_tokens"] is None for r in rows) or None in self.rates[:2]:
            return None
        total = Decimal(0)
        for row in rows:
            cached = row["cached_input_tokens"]
            if cached and self.rates[2] is None:
                return None
            # A provider not reporting cache breakdown can still be estimated
            # using the configured standard input rate; this is an estimate.
            cached = cached or 0
            total += ((row["input_tokens"] - cached) * self.rates[0] +
                      row["output_tokens"] * self.rates[1] + cached * (self.rates[2] if self.rates[2] is not None else self.rates[0])) / Decimal(1_000_000)
        return str(total)

    def summary(self):
        groups = {}
        for call in self.calls:
            groups.setdefault((call["provider"], call["model"]), []).append(call)
        def counts(rows):
            return {"calls": len(rows), "input_tokens": None if any(r["input_tokens"] is None for r in rows) else sum(r["input_tokens"] for r in rows),
                    "output_tokens": None if any(r["output_tokens"] is None for r in rows) else sum(r["output_tokens"] for r in rows),
                    "unknown_usage_calls": sum(r["input_tokens"] is None or r["output_tokens"] is None for r in rows),
                    "estimated_cost_usd": self._cost(rows)}
        return {**counts(self.calls), "cache_hits": self.cache_hits, "budget_skips": self.budget_skips,
                "pricing_source": "USER_CONFIGURED" if all(x is not None for x in self.rates[:2]) else "NOT_CONFIGURED",
                "per_model": [{"provider": p, "model": m, **counts(rows)} for (p, m), rows in sorted(groups.items())],
                "cached_build_usage": counts([row for history in self.build_usage.values() for row in history])}
