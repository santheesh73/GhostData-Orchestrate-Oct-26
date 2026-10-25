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
        if re.search(r'[`"“”]|ignore .*instructions|system prompt', normalized):
            return Intent(Authorization.UNRESOLVED, "QUOTED_OR_HYPOTHETICAL_REQUEST")
        for subject, deletion, cue, negative in (
            (r"アカウント|個人情報", r"削除", r"削除(?:を|の)?(?:依頼|お願い|要求)|削除して(?:ください|ほしい)", r"削除しない|削除せず|削除を希望しません|削除しません"),
            (r"계정|개인정보", r"삭제", r"삭제(?:를)?\s*(?:요청|부탁)|삭제해\s?주세요", r"삭제하지|삭제를 원하지|삭제\s?말"),
        ):
            if re.search(subject, normalized) and re.search(deletion, normalized):
                if re.search(negative, normalized):
                    return Intent(Authorization.NON_DELETION, "EXPLICIT_NEGATED_DELETION")
                if re.search(cue, normalized):
                    return Intent(Authorization.DELETION, "EXPLICIT_MULTILINGUAL_DELETION_REQUEST")
        return Intent(Authorization.UNRESOLVED, "UNSUPPORTED_REQUEST_LANGUAGE")
    # Explicitly unsupported interpretation; do not execute instructions nested
    # inside a quoted example, a role override, or a hypothetical question.
    if re.search(r'`|\b(ignore (?:all |previous |prior )?instructions|system prompt|if i|hypothetical|what happens if|how (?:do|can) i)\b', normalized):
        return Intent(Authorization.UNRESOLVED, "QUOTED_OR_HYPOTHETICAL_REQUEST")
    # A quoted UI label is not a quoted command. Remove only balanced benign
    # labels; erasure commands within quotations remain explicitly unresolved.
    quoted = re.findall(r'"([^"\n]*)"|“([^”\n]*)”', normalized)
    if any(re.search(r"\b(delete|deletion|erase|erasure|remove|eliminar|supprimer)\b", a or b) for a, b in quoted):
        return Intent(Authorization.UNRESOLVED, "QUOTED_OR_HYPOTHETICAL_REQUEST")
    normalized = re.sub(r'"[^"\n]*"|“[^”\n]*”', " ", normalized)
    if re.search(r'["“”]', normalized):
        return Intent(Authorization.UNRESOLVED, "QUOTED_OR_HYPOTHETICAL_REQUEST")
    if re.search(r"\b(someone else's|another person's|their account|his account|her account)\b", normalized):
        return Intent(Authorization.UNRESOLVED, "THIRD_PARTY_SCOPE")
    account_context = bool(re.search(r"\b(account|profile|cuenta|conta|compte)\b", normalized))
    self_deletion_history = bool(re.search(r"\bi (?:have )?(?:deleted|closed|erased) (?:my |this |the )?(?:account|profile|personal (?:data|information))\b", normalized))
    sentences = re.split(r"[.!?;\n]+|\bbut\b", normalized)
    positive, negative, other, unresolved_mention = False, False, False, False
    for sentence in sentences:
        subject = re.search(r"\b(account|profile|personal (?:data|information)|records|conta|dados pessoais|cuenta|datos personales|compte|donnees personnelles|konto)\b", sentence)
        if account_context and re.search(r"\b(search result|export file|my name|my contact details)\b", sentence):
            subject = True
        continuation = account_context and re.search(r"\b(finish|complete|continue|completar)\b.*\b(deletion|erasure|eliminaci[oó]n)\b", sentence)
        if continuation:
            subject = True
        deletion = re.search(r"\b(delete[ds]?|deleting|deletion|erase[ds]?|erasing|erasure|remove[ds]?|removing|exclus[aã]o|excluir|apagar|eliminar|eliminaci[oó]n|borrar|suppression|supprimer|effacer|loeschen|löschen)\b", sentence)
        permanent_closure = re.search(r"\bclose (?:my |this |the )?account (?:permanently|completely)\b", sentence)
        verification = self_deletion_history and re.search(r"\b(verify|confirm|check|ensure)\b.*\b(gone|absent|removed|deleted|erased)\b", sentence)
        deletion = deletion or permanent_closure or verification
        negated = re.search(r"\b(do not|don't|not (?:asking|a request|requesting)|without|never|n[aã]o|no (?:quiero|solicito|eliminen|borren|completen|completar)|ne .* pas)\b", sentence)
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
                cue = re.search(r"\b(please|would like|i (?:request|am requesting|want|am asking)|could you|can you|solicito|je demande|pueden)\b|\bi(?: am|'m) (?:deleting|erasing|removing)\b", sentence)
                imperative = re.match(r"\s*(delete|erase|remove|close|excluir|apagar|eliminar|borrar|supprimer|effacer|loeschen|löschen)\b", sentence)
                if re.search(r"\b(?:does|what|when|explain|policy says|for example|said|already|previously)\b", sentence) and not verification:
                    unresolved_mention = True
                    continue
                if re.search(r"\b(?:whether|if)\b", sentence) and not self_deletion_history and not continuation:
                    unresolved_mention = True
                    continue
                # An explicit request/imperative is needed, not just a mention.
                if cue or imperative:
                    positive = True
                else:
                    unresolved_mention = True
    if positive and negative:
        return Intent(Authorization.UNRESOLVED, "CONFLICTING_AUTHORIZATION")
    if positive:
        return Intent(Authorization.DELETION, "EXPLICIT_DELETION_REQUEST")
    # Continuing an explicitly personal privacy/deletion review can authorize
    # verification without repeating an imperative erasure command. A bare
    # status/policy question has no prior-request context and stays unresolved.
    review = (account_context and re.search(r"\b(my|i)\b", normalized)
              and re.search(r"\b(request|report|told|before deleting)\b", normalized)
              and re.search(r"\b(privacy|delet\w*|eras\w*|gone|removed)\b", normalized)
              and re.search(r"\bplease (?:check|inspect|confirm|handle)\b", normalized))
    if review and not negative:
        return Intent(Authorization.DELETION, "CONTINUING_PERSONAL_DELETION_REVIEW")
    if unresolved_mention:
        return Intent(Authorization.UNRESOLVED, "UNSCOPED_DELETION_MENTION")
    if other or negative:
        return Intent(Authorization.NON_DELETION, "EXPLICIT_OTHER_OR_NEGATED_DELETION")
    return Intent(Authorization.UNRESOLVED, "INTENT_NOT_ESTABLISHED")
