#!/usr/bin/env python3
"""yt-facts: every substantive sentence of a script and every on-screen number has a claim id.

claims.json (schema yt-facts/1):
  {"schema": "yt-facts/1", "claims": [{"id": "C1", "tier": "original|media|org|science|observation|hypothesis",
     "text": "...", "attribution": "Bloomberg", "date": "2024-04-09", "url": "https://...", "confidence": "high|medium|low",
     "evidence": "relative/path (observation)", "forbid": ["words that must not appear next to this claim"],
     "wording": "required attribution phrase for media/org claims, e.g. 'reported'"}]}
script.md: factual sentences end with {C1} or {C1,C4}; a limitation ("we cannot ...") ends with {L}. Headings, [directions] and bracketed lines are skipped.
Exit 0 = pass, 1 = blocked. Blocking is the point: a missing proof is reported, never invented.
"""
import argparse, json, os, re, sys

TIERS = {"original", "media", "org", "science", "observation", "hypothesis"}
CONF = {"high": 3, "medium": 2, "low": 1}
# words that assert more than most evidence allows; a sentence using one needs a claim that lists it in "allow"
STRONG = ["prove", "proves", "proven", "proof", "reveal", "reveals", "revealed", "confirm", "confirms", "confirmed",
          "collapsed", "cancelled", "canceled", "abandoned", "built", "completed", "finished"]
TAG = re.compile(r"\{(C\d+(?:\s*,\s*C\d+)*)\}")
HAS_NUMBER = re.compile(r"\d")


def load_claims(path):
    d = json.load(open(path, encoding="utf-8"))
    if d.get("schema") != "yt-facts/1":
        raise ValueError("claims.json: schema must be yt-facts/1")
    by = {}
    for c in d["claims"]:
        for k in ("id", "tier", "text", "confidence"):
            if k not in c:
                raise ValueError(f"claim {c.get('id')}: missing {k}")
        if c["tier"] not in TIERS or c["confidence"] not in CONF:
            raise ValueError(f"claim {c['id']}: bad tier/confidence")
        if c["id"] in by:
            raise ValueError(f"duplicate claim id {c['id']}")
        by[c["id"]] = c
    return by


def check_claims(claims, root=".", defer_evidence=False):
    """Registry-level problems (independent of any script)."""
    probs = []
    for c in claims.values():
        i = c["id"]
        if c["tier"] in ("media", "org", "science") and not (c.get("attribution") and c.get("url") and c.get("date")):
            probs.append(f"{i}: {c['tier']} claim needs attribution, date and url")
        if c["tier"] == "observation" and not defer_evidence:
            ev = c.get("evidence")
            if not ev or not os.path.exists(os.path.join(root, ev)):
                probs.append(f"{i}: observation needs an existing evidence file (got {ev!r})")
        if c["tier"] in ("media", "org") and not c.get("wording"):
            probs.append(f"{i}: {c['tier']} claim needs 'wording' (e.g. 'reported', 'said')")
        if c["tier"] == "hypothesis" and c["confidence"] != "low":
            probs.append(f"{i}: a hypothesis must have confidence low")
    return probs


def lint_script(text, claims, min_conf="medium"):
    """Return (problems, used_ids, stats). A sentence is 'factual' if it has a number or a STRONG word."""
    probs, used = [], set()
    n_fact = n_tagged = 0
    for ln, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(("#", "[", ">", "---", "<!--")):
            continue
        for sent in re.split(r"(?<=[.!?])\s+(?!\{)|(?<=\})\s+(?=[A-Z\"])", s):
            if not sent.strip():
                continue
            if "{L}" in sent:                       # explicit limitation: must be a negation, then nothing is asserted
                plain_l = sent.replace("{L}", "")
                if re.search(r"\b(not|cannot|can't|no|never|nothing|without)\b", plain_l, re.I):
                    n_fact += 1; n_tagged += 1
                else:
                    probs.append(f"line {ln}: {{L}} is only for limitations (needs not/cannot/no): {plain_l.strip()[:70]!r}")
                continue
            tags = TAG.findall(sent)
            ids = [t.strip() for g in tags for t in g.split(",")]
            plain = TAG.sub("", sent)
            words = {w.lower().strip(".,;:!?\"'") for w in plain.split()}
            strong = sorted(words & set(STRONG))
            factual = bool(HAS_NUMBER.search(plain)) or bool(strong)
            if factual:
                n_fact += 1
            if ids:
                n_tagged += 1
            if factual and not ids:
                probs.append(f"line {ln}: factual sentence without a claim id: {plain.strip()[:80]!r}")
            for i in ids:
                c = claims.get(i)
                if c is None:
                    probs.append(f"line {ln}: unknown claim id {i}")
                    continue
                used.add(i)
                if c["tier"] != "hypothesis" and CONF[c["confidence"]] < CONF[min_conf]:
                    probs.append(f"line {ln}: {i} has confidence {c['confidence']} (< {min_conf}); reword or drop")
                if c["tier"] in ("media", "org") and c.get("wording") and c["wording"].lower() not in plain.lower():
                    probs.append(f"line {ln}: {i} is a {c['tier']} claim; the sentence must contain {c['wording']!r}")
                if c["tier"] == "hypothesis" and not re.search(r"\b(may|might|could|consistent with|suggests?|we can't|cannot)\b", plain, re.I):
                    probs.append(f"line {ln}: {i} is a hypothesis; hedge it (may/could/consistent with)")
                for f in c.get("forbid") or []:
                    if re.search(r"\b" + re.escape(f) + r"\b", plain, re.I):
                        probs.append(f"line {ln}: {i} forbids the word {f!r}")
            for w in strong:
                if ids and not any(w in [a.lower() for a in claims[i].get("allow", [])] for i in ids if i in claims):
                    probs.append(f"line {ln}: strong word {w!r} not allowed by {','.join(ids)} (add to the claim's 'allow' only if the evidence supports it)")
    return probs, sorted(used), {"factual_sentences": n_fact, "tagged_sentences": n_tagged}


def lint_labels(labels, claims, min_conf="medium"):
    """On-screen labels: each {text, claim?}. A label with a digit needs a claim; the claim must exist."""
    probs = []
    for lab in labels:
        for cid in lab.get("claims") or []:
            if cid not in claims:
                probs.append(f"label {lab.get('text')!r}: unknown claim {cid}")
            elif claims[cid]["tier"] != "hypothesis" and CONF[claims[cid]["confidence"]] < CONF[min_conf]:
                probs.append(f"label {lab.get('text')!r}: claim {cid} confidence below {min_conf}")
        if lab.get("claims"):
            continue
        if str(lab.get("text", "")).startswith("graphic:"):
            if not lab.get("exempt"):
                probs.append(f"{lab['text']}: graphic declares no claims (set assets.<id>.claims or exempt)")
            continue
        t, cid = lab.get("text", ""), lab.get("claim")
        if cid and cid not in claims:
            probs.append(f"label {t!r}: unknown claim {cid}")
        elif HAS_NUMBER.search(t) and not cid and not lab.get("exempt"):
            probs.append(f"label {t!r}: contains a number but has no claim id")
        elif cid and CONF[claims[cid]["confidence"]] < CONF[min_conf]:
            probs.append(f"label {t!r}: claim {cid} confidence below {min_conf}")
    return probs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--claims", required=True)
    ap.add_argument("--script")
    ap.add_argument("--labels", help="json list of {text, claim} from yt-storyboard")
    ap.add_argument("--root", default=".", help="folder that evidence paths are relative to")
    ap.add_argument("--defer-evidence", action="store_true", help="registry check before the evidence stage exists")
    ap.add_argument("--min-confidence", default="medium", choices=list(CONF))
    a = ap.parse_args(argv)
    try:
        claims = load_claims(a.claims)
    except (OSError, ValueError, KeyError) as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        return 1
    probs = check_claims(claims, a.root, a.defer_evidence)
    used, stats = [], {}
    if a.script:
        p, used, stats = lint_script(open(a.script, encoding="utf-8").read(), claims, a.min_confidence)
        probs += p
    if a.labels:
        probs += lint_labels(json.load(open(a.labels)), claims, a.min_confidence)
    res = {"status": "blocked" if probs else "ok", "claims": len(claims), "used": used, "stats": stats, "problems": probs}
    print(json.dumps(res, indent=1))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
