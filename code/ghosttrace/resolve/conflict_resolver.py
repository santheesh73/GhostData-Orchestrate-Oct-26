"""Resolve each dimension by observation time, preserving equal-time conflicts.

Only direct state observations enter this function. There is no global ranking
of SQL, JSON, logs, or evidence ID spelling. Physical copies are grouped outside
this function and cannot cancel each other's findings.
"""

from collections import defaultdict

from .models import ResolvedFact


def resolve_facts(facts):
    dimensions = defaultdict(list)
    for fact in facts:
        dimensions[fact.dimension].append(fact)
    result = []
    for dimension, candidates in sorted(dimensions.items()):
        latest = max(f.observed_at for f in candidates)
        current = [f for f in candidates if f.observed_at == latest]
        values = tuple(sorted({f.value_json for f in current}))
        result.append(ResolvedFact(dimension, values[0] if len(values) == 1 else None, latest,
            tuple(sorted({f.observation_id for f in current})), values if len(values) > 1 else ()))
    return tuple(result)
