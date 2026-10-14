"""Grammatical on-screen phrases cut from the narration (number-card kickers, event-year labels).

Rule (EP003 review): a dynamic label is a CONTIGUOUS piece of the spoken sentence, starts at a clause boundary (sentence start,
after , ; : or a connector such as 'that'/'and'), never starts with a word that needs a head before it ('by', 'of', 'that') and,
for labels that stand alone, never ends with a dangling word ('the', 'at', 'was'). Words are never dropped from the middle.
`lint` checks any label against the narration so the director report can list every dynamic text with a verdict.
"""
import re

CONNECT = {"that", "and", "but", "so", "which", "because", "when", "while", "where", "or"}
START_BAD = {"by", "of", "to", "with", "than", "that", "which", "and", "or", "but", "so", "as", "from", "for"}
START_STRIP = {"a", "an", "the", "at", "in", "on", "by", "of", "its", "their", "his", "her", "to", "and", "but", "so", "then", "or"}
END_BAD = {"the", "a", "an", "of", "to", "in", "on", "at", "by", "for", "with", "and", "or", "but", "that", "its", "their", "his", "her",
           "than", "from", "as", "is", "was", "were", "are", "be", "been", "has", "have", "had", "about", "almost", "nearly", "more", "less"}


def bare(t):
    return re.sub(r"[^\w'\-%$]", "", t).lower()


def _clean(t):
    return re.sub(r"[^\w'\-%$]", "", t)


def boundaries(tokens):
    b = [0]
    for k, t in enumerate(tokens[:-1]):
        if re.search(r"[,;:]$", t) or bare(t) in CONNECT: b.append(k + 1)
    return sorted(set(b))


def clause_suffix(tokens, max_words=9, max_chars=None):
    """the longest clause-initial suffix of `tokens` with at most max_words words (and max_chars characters) that does not start with a
    dangling word; [] if none"""
    for b in boundaries(tokens):
        cand = tokens[b:]
        if 0 < len(cand) <= max_words and bare(cand[0]) not in START_BAD and (max_chars is None or len(" ".join(cand)) <= max_chars): return cand
    return []


def _strip(tokens, ends=True):
    while tokens and bare(tokens[0]) in START_STRIP: tokens = tokens[1:]
    while ends and tokens and bare(tokens[-1]) in END_BAD: tokens = tokens[:-1]
    return tokens


def label(pre, post, max_words=4):
    """label for a year: the clause before it (minus the preposition the caller removed), else the words after it up to the clause end"""
    pre = list(pre)
    dig = max((k + 1 for k, t in enumerate(pre) if re.search(r"\d", t)), default=0); pre = pre[dig:]          # never across another number
    if pre and re.search(r"[,;:]$", pre[-1]): pre = []                                                        # the clause ended before the year
    cand = _strip(clause_suffix(pre, 99) if pre else [], ends=False)
    if len(cand) > max_words: cand = _strip(cand[-max_words:], ends=False)
    cand = _strip(cand)
    if not cand:
        p = []
        for t in post:
            if re.search(r"\d", t): break
            p.append(t)
            if re.search(r"[,;:.!?]$", t): break
        cand = _strip(_strip(p)[:max_words])
    return " ".join(_clean(t) for t in cand).strip()


def lint(text, narration_tokens, standalone=True):
    """problems of one on-screen phrase: must be contiguous narration words, no dangling start (and end, if standalone)"""
    words = [bare(t) for t in text.split() if bare(t)]
    if not words: return []
    nar = [bare(t) for t in narration_tokens]
    contiguous = any(nar[i:i + len(words)] == words for i in range(len(nar) - len(words) + 1))
    p = []
    if not contiguous: p.append("not a contiguous piece of the narration")
    if words[0] in START_BAD: p.append(f"starts with '{words[0]}'")
    if standalone and words[-1] in END_BAD: p.append(f"ends with '{words[-1]}'")
    return p
