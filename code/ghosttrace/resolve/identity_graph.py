"""A temporal ownership graph, deliberately not a transitive union of aliases.

Audit changes define half-open ownership intervals. Current snapshots lacking an
availability clock are candidate context only. Exact stable-ID/identifier pairs
in eligible business records establish point observations, not lifelong ownership.
"""

from collections import defaultdict
from types import MappingProxyType

from ..ingest.normalization import normalize_identifier
from ..models import Uncertainty
from .models import IdentityResolution, Ownership
from .signals import STRONG_KINDS, aware, eligible, paired_aliases, payload, signals
from .temporal_replay import extract_facts


def _value(kind, value):
    return normalize_identifier(kind, value) if isinstance(value, str) and value.strip() and value.casefold() not in {"null", "none"} else ""


def _ownership_key(o):
    return (o.kind, o.value, o.user_id, o.valid_from.isoformat() if o.valid_from else "",
            o.valid_until.isoformat() if o.valid_until else "", o.basis, o.observation_ids)


class IdentityGraph:
    def __init__(self, observations, *, cache_context=True):
        self.cache_context = cache_context
        self.observations = tuple(observations)
        self.payloads = {o.observation_id: payload(o) for o in self.observations}
        self.known_users = frozenset(p["user_id"] for o in self.observations
            if o.claim_kind in {"IDENTITY_CONTEXT", "IDENTITY_CHANGE_CLAIM"}
            and isinstance((p := self.payloads[o.observation_id]).get("user_id"), str) and p["user_id"])
        self.subject_signals = {o.observation_id: signals(self.payloads[o.observation_id], self.known_users)
                                for o in self.observations}
        self.pairs = {o.observation_id: paired_aliases(self.payloads[o.observation_id], self.known_users)
                      for o in self.observations}
        self.context_records = tuple(o for o in self.observations if o.claim_kind == "IDENTITY_CONTEXT")
        self.history_records = tuple(o for o in self.observations if o.claim_kind == "IDENTITY_CHANGE_CLAIM")
        self.pair_records = tuple(o for o in self.observations
            if len(self.subject_signals[o.observation_id][0]) == 1
            and self.pairs[o.observation_id]
            and {f.value_json for f in extract_facts(o) if f.dimension == "presence"} == {'"PRESENT"'})
        self.context_users = frozenset(self.payloads[o.observation_id].get("user_id") for o in self.context_records)
        if cache_context:
            # These undated candidates never become temporal proof. Share only
            # immutable normalization/index work within this fixed input graph.
            context = []
            for observation in self.context_records:
                data = self.payloads[observation.observation_id]
                user = data.get("user_id", "")
                for kind in sorted(STRONG_KINDS):
                    value = _value(kind, data.get(kind))
                    if user and value:
                        context.append(Ownership(user, kind, value, None, None, None,
                            (observation.observation_id,), "SNAPSHOT_CONTEXT", certain=False))
            self.cached_context = tuple(sorted(context, key=_ownership_key))
            by_alias, by_user = defaultdict(list), defaultdict(list)
            for owner in self.cached_context:
                by_alias[(owner.kind, owner.value)].append(owner)
                by_user[owner.user_id].append(owner)
            self.context_aliases = MappingProxyType({key: tuple(value) for key, value in by_alias.items()})
            self.context_by_user = MappingProxyType({key: tuple(value) for key, value in by_user.items()})

    def at(self, cutoff):
        aware(cutoff)
        ownership, context, issues = [], [], defaultdict(list)
        changes = defaultdict(list)
        known_at_cutoff = set(self.context_users)
        known_at_cutoff.update(self.payloads[o.observation_id].get("user_id") for o in self.history_records
                               if eligible(o, cutoff) == "ELIGIBLE")
        if self.cache_context:
            context = self.cached_context
        records = (*(() if self.cache_context else self.context_records), *self.history_records, *self.pair_records)
        for observation in records:
            data = self.payloads[observation.observation_id]
            if observation.claim_kind == "IDENTITY_CONTEXT":
                user = data.get("user_id", "")
                for kind in sorted(STRONG_KINDS):
                    value = _value(kind, data.get(kind))
                    if user and value:
                        # updated_at is a modification fact, not file availability.
                        context.append(Ownership(user, kind, value, None, None, None,
                                                 (observation.observation_id,), "SNAPSHOT_CONTEXT", certain=False))
                continue
            if eligible(observation, cutoff) != "ELIGIBLE":
                continue
            if observation.claim_kind == "IDENTITY_CHANGE_CLAIM":
                user, kind = data.get("user_id"), data.get("field_name")
                if user and kind in STRONG_KINDS:
                    changes[(user, kind)].append(observation)
            elif observation.claim_kind in {"RECORD_SNAPSHOT", "SQL_RECORD", "LOG_EVENT"}:
                # Future-only registry entries must still be excluded. Reuse
                # pairs only when the eligible registry is exactly unchanged.
                pairs = (self.pairs[observation.observation_id] if self.cache_context and known_at_cutoff == self.known_users
                         else paired_aliases(data, known_at_cutoff))
                for user, kind, value in pairs:
                    ownership.append(Ownership(user, kind, value, observation.observed_at,
                        observation.observed_at, observation.evidence.available_at,
                        (observation.observation_id,), "OBSERVED_PAIR", point=True))
        for (user, kind), observations in sorted(changes.items()):
            by_time = defaultdict(list)
            for observation in observations:
                by_time[observation.observed_at].append(observation)
            transitions = []
            broken = False
            for clock, group in sorted(by_time.items()):
                variants = defaultdict(list)
                for observation in group:
                    data = self.payloads[observation.observation_id]
                    variants[(_value(kind, data.get("old_value")), _value(kind, data.get("new_value")))].append(observation)
                if len(variants) > 1:
                    broken = True
                    issues[user].append(Uncertainty("CONFLICTING_IDENTITY_HISTORY",
                                                   "different identity changes share one timestamp"))
                for (old, new), proof in sorted(variants.items()):
                    transitions.append((clock, old, new, tuple(sorted(o.observation_id for o in proof)),
                                        max(o.evidence.available_at for o in proof)))
            for previous, current in zip(transitions, transitions[1:]):
                if previous[2] != current[1]:
                    broken = True
                    issues[user].append(Uncertainty("BROKEN_IDENTITY_HISTORY", "adjacent old/new identity values disagree"))
            # A broken chain remains candidate ownership, never silently repaired.
            first = transitions[0]
            if first[1]:
                ownership.append(Ownership(user, kind, first[1], None, first[0], first[4], first[3],
                                           "AUDIT_HISTORY", certain=not broken))
            for i, (clock, old, new, proof, available) in enumerate(transitions):
                end = transitions[i + 1][0] if i + 1 < len(transitions) else None
                interval_proof, interval_available = proof, available
                if end is not None:
                    interval_proof = tuple(sorted(set(proof + transitions[i + 1][3])))
                    interval_available = max(available, transitions[i + 1][4])
                if new:
                    ownership.append(Ownership(user, kind, new, clock, end, interval_available, interval_proof,
                                               "AUDIT_HISTORY", certain=not broken))
                if broken and old:
                    ownership.append(Ownership(user, kind, old, None, clock, available, proof,
                                               "AUDIT_HISTORY", certain=False))
        return IdentityView(cutoff, ownership, context, issues, frozenset(known_at_cutoff),
                            context_index=self.context_aliases if self.cache_context else None,
                            context_by_user=self.context_by_user if self.cache_context else None)


class IdentityView:
    def __init__(self, cutoff, ownership, context, issues, known_users, *, context_index=None, context_by_user=None):
        self.cutoff = cutoff
        self.known_users = known_users
        self.ownership = tuple(sorted(ownership, key=_ownership_key))
        self.context = tuple(context) if context_index is not None else tuple(sorted(context, key=_ownership_key))
        self.context_by_user = context_by_user
        self.issues = issues
        if context_index is None:
            self.by_alias = defaultdict(list)
            for owner in (*self.ownership, *self.context):
                self.by_alias[(owner.kind, owner.value)].append(owner)
        else:
            self.by_alias = dict(context_index)
            proven = defaultdict(list)
            for owner in self.ownership:
                proven[(owner.kind, owner.value)].append(owner)
            for key, owners in proven.items():
                self.by_alias[key] = (*owners, *self.by_alias.get(key, ()))

    def owners(self, kind, value, *, at=None, include_context=False):
        if at is not None:
            aware(at)
        candidates = self.by_alias.get((kind, normalize_identifier(kind, value)), ())
        return tuple(o for o in candidates if (include_context or o.basis != "SNAPSHOT_CONTEXT")
                     and (at is None or o.contains(at)))

    def identifiers_for(self, user):
        if self.context_by_user is not None:
            return (*tuple(o for o in self.ownership if o.user_id == user), *self.context_by_user.get(user, ()))
        return tuple(o for o in (*self.ownership, *self.context) if o.user_id == user)

    def possible_owners(self, kind, value, observed_at):
        """Keep stale historical owners, but never propagate a later assignment
        backwards. A current snapshot cannot override an explicit audit bound.
        After alias reuse, a stale record needs a stable reference to disambiguate.
        """
        all_matches = self.owners(kind, value, include_context=True)
        bounded_users = {o.user_id for o in all_matches if o.basis == "AUDIT_HISTORY"}
        return tuple(o for o in all_matches
            if (o.basis == "SNAPSHOT_CONTEXT" and o.user_id not in bounded_users)
            or (o.basis != "SNAPSHOT_CONTEXT" and (o.valid_from is None or o.valid_from <= observed_at)))

    def resolve(self, request):
        aware(request.requested_at)
        aware(request.audit_at)
        if request.requested_at > request.audit_at or request.audit_at != self.cutoff:
            raise ValueError("request times do not match the reconstruction cutoff")
        all_matches = self.owners("email", request.email, include_context=True)
        proven = tuple(o for o in all_matches if o.basis != "SNAPSHOT_CONTEXT"
                       and (o.valid_from is None or o.valid_from <= request.requested_at))
        active = tuple(o for o in proven if o.certain and o.contains(request.requested_at))
        # Prefer an owner at request time when an address has been reassigned.
        selected = active or proven
        users = {o.user_id for o in selected}
        contextual = {o.user_id for o in all_matches if o.basis == "SNAPSHOT_CONTEXT"}
        uncertainties = []
        if not users:
            users = contextual
            status = "CONTEXT_ONLY" if len(users) == 1 else "AMBIGUOUS" if users else "UNRESOLVED"
            if users:
                uncertainties.append(Uncertainty("SNAPSHOT_AVAILABILITY_UNKNOWN",
                                                 "current snapshot identifies candidates without a capture clock"))
        elif len(users) > 1:
            status = "AMBIGUOUS"
        elif any(not o.certain for o in selected):
            status = "AMBIGUOUS"
        else:
            status = "RESOLVED"
        for user in sorted(users):
            uncertainties.extend(self.issues.get(user, ()))
        if status == "AMBIGUOUS":
            uncertainties.append(Uncertainty("AMBIGUOUS_IDENTITY", "ownership is not uniquely supported at the required time"))
        if not users:
            uncertainties.append(Uncertainty("IDENTITY_NOT_FOUND", "no exact current or historical email link"))
        user = next(iter(users)) if len(users) == 1 else None
        owners = self.identifiers_for(user) if user else all_matches
        return IdentityResolution(status, user, tuple(sorted(users)), owners,
                                  tuple(sorted(set(uncertainties), key=lambda u: (u.code, u.detail))))
