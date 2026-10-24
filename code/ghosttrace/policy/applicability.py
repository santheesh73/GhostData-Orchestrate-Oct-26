"""Conservative deterministic intent parsing; unknown language/scope defers.

Patterns describe request grammar, not full sample sentences. Negation, quoted
commands, hypothetical requests and conflicting scopes block deletion. Evidence
files and reported workflow status never determine request authorization.
"""

import re
import unicodedata

from ..models import Authorization
from .models import Intent


def classify_request(text):
    normalized = unicodedata.normalize("NFKC", text).casefold().replace("’", "'")
    normalized = re.sub(r"[‐‑–—-]", " ", normalized)
    if not normalized.strip():
        return Intent(Authorization.UNRESOLVED, "EMPTY_REQUEST")
    if any(unicodedata.category(char).startswith("L") and "LATIN" not in unicodedata.name(char, "") for char in normalized):
        return Intent(Authorization.UNRESOLVED, "UNSUPPORTED_REQUEST_LANGUAGE")
    # Explicitly unsupported interpretation; do not execute instructions nested
    # inside a quoted example, a role override, or a hypothetical question.
    if re.search(r'[`"“”]|\b(ignore (?:all |previous |prior )?instructions|system prompt|if i|hypothetical|what happens if|how (?:do|can) i)\b', normalized):
        return Intent(Authorization.UNRESOLVED, "QUOTED_OR_HYPOTHETICAL_REQUEST")
    sentences = re.split(r"[.!?;\n]+|\bbut\b", normalized)
    positive, negative, other, unresolved_mention = False, False, False, False
    for sentence in sentences:
        subject = re.search(r"\b(account|profile|personal (?:data|information)|records|conta|dados pessoais|cuenta|datos personales|compte|donnees personnelles|konto)\b", sentence)
        deletion = re.search(r"\b(delete[ds]?|deleting|deletion|erase[ds]?|erased|erasure|remove[ds]?|removing|exclus[aã]o|excluir|apagar|eliminar|eliminaci[oó]n|borrar|suppression|supprimer|effacer|loeschen|löschen)\b", sentence)
        negated = re.search(r"\b(do not|don't|not (?:asking|a request|requesting)|without|never|n[aã]o|no (?:quiero|solicito|eliminen|borren)|ne .* pas)\b", sentence)
        other_action = re.search(r"\b(copy|download|export|portable|access|reset|correct|correction|replace|change|unsubscribe|marketing|promotional|information request|opt out)\b", sentence)
        scoped_other = re.search(r"\b(marketing|promotional|mailing|newsletter)\b", sentence)
        if other_action:
            other = True
        if deletion and negated:
            negative = True
            continue
        if deletion and subject:
            if negated:
                negative = True
            elif not scoped_other:
                # Questions about policy are not affirmative deletion requests.
                if re.search(r"\b(?:does|what|when|explain|policy says|for example|said|already|previously)\b", sentence):
                    return Intent(Authorization.UNRESOLVED, "DESCRIPTIVE_DELETION_TEXT")
                # An explicit request/imperative is needed, not just a mention.
                if re.search(r"\b(please|would like|i (?:request|am requesting|want|am asking)|could you|can you|solicito|je demande)\b", sentence) or re.match(r"\s*(delete|erase|remove|excluir|apagar|eliminar|borrar|supprimer|effacer|loeschen|löschen)\b", sentence):
                    positive = True
                else:
                    unresolved_mention = True
    if positive and negative:
        return Intent(Authorization.UNRESOLVED, "CONFLICTING_AUTHORIZATION")
    if positive:
        return Intent(Authorization.DELETION, "EXPLICIT_DELETION_REQUEST")
    if unresolved_mention:
        return Intent(Authorization.UNRESOLVED, "UNSCOPED_DELETION_MENTION")
    if other or negative:
        return Intent(Authorization.NON_DELETION, "EXPLICIT_OTHER_OR_NEGATED_DELETION")
    return Intent(Authorization.UNRESOLVED, "INTENT_NOT_ESTABLISHED")
