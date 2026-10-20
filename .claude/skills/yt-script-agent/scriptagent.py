#!/usr/bin/env python3
"""yt-script-agent: the writing brief and the acceptance gate for a documentary script (American English, 6-9 minutes).

The agent (Claude) writes script.md. This tool does the parts code can do honestly:
  brief     research claims -> chapter skeleton, claim assignment, word budget, style rules -> tasks/script.md + research/brief.json
  validate  length (words / 2.45 wps), structure, hook, repetition/padding, claim coverage, then yt-facts lint -> pass/blocked with reasons
It never writes prose. If the verified facts cannot carry 6 minutes it says INSUFFICIENT_FACTS instead of padding.
"""
import argparse, collections, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FACTS = os.path.join(HERE, "..", "yt-facts", "facts.py")
WPS = 2.45
MIN_S, MAX_S = 360, 540            # 6-9 minutes
TAG = re.compile(r"\{(?:C\d+(?:\s*,\s*C\d+)*|L)\}")
CH_RE = re.compile(r"^##\s+([a-z0-9_]+)\s*[:\-]\s*(.*)$")
STYLE = ["American English, spoken, second person plural 'we' for the investigation", "hook in the first 45 words: a concrete contrast, no throat-clearing",
         "one idea per sentence; no filler transitions; never repeat a fact to fill time", "keep PROMISED / REPORTED / OBSERVED apart in every chapter",
         "media/org claims contain their wording word (reported/said); hypotheses are hedged; limitations end with {L}",
         "no 'proves', 'reveals', 'collapsed', 'cancelled', 'built' unless a claim explicitly allows it", "explain US-specific references in a few words"]


TITLES = {"method": "How we looked", "shows": "What the satellites show", "segment": "The dark segment", "checks": "How we tried to break it"}


def skeleton(claims):
    """Chapter plan from the claim set: hook, promise (original), plan (media/org), method (science), evidence groups (observation), limits, close."""
    by = collections.defaultdict(list)
    for c in claims:
        by[c["tier"]].append(c)
    groups = collections.OrderedDict()
    for c in by["observation"]:
        groups.setdefault(c.get("group") or "shows", []).append(c)
    ch = [("hook", "The first fifteen seconds", [c["id"] for c in by["original"][:1]] + [c["id"] for c in by["observation"][:1]])]
    if by["original"]:
        ch.append(("promise", "The promise", [c["id"] for c in by["original"]]))
    if by["media"] or by["org"]:
        ch.append(("plan", "What has been reported", [c["id"] for c in by["media"] + by["org"] if c["confidence"] != "low"]))
    meth = [c["id"] for c in by["science"]] + [c["id"] for c in by["observation"] if c.get("group") == "method"]
    if meth:
        ch.append(("method", TITLES["method"], meth))
    for g, cs in groups.items():
        if g != "method":
            ch.append((g, TITLES.get(g, g.replace("_", " ").capitalize()), [c["id"] for c in cs]))
    ch.append(("limits", "What we cannot say", [c["id"] for c in by["hypothesis"]]))
    ch.append(("close", "What to watch", []))
    return [{"id": i, "title": t, "claims": cl} for i, t, cl in ch]


def brief(root):
    cl = json.load(open(os.path.join(root, "claims.json")))["claims"]
    usable = [c for c in cl if c["confidence"] in ("medium", "high") or c["tier"] == "hypothesis"]
    capacity = len([c for c in cl if c["confidence"] in ("medium", "high")]) * 55
    sk = skeleton(usable)
    b = {"schema": "yt-script-brief/1", "target_seconds": [MIN_S, MAX_S], "target_words": [int(MIN_S * WPS), int(MAX_S * WPS)],
         "factual_capacity_words": capacity, "insufficient_facts": capacity < MIN_S * WPS * 0.8,
         "chapters": sk, "style": STYLE, "do_not_use": [c["id"] for c in cl if c["confidence"] == "low" and c["tier"] != "hypothesis"],
         "claims": {c["id"]: {"tier": c["tier"], "confidence": c["confidence"], "text": c["text"], "wording": c.get("wording")} for c in usable}}
    os.makedirs(os.path.join(root, "research"), exist_ok=True)
    json.dump(b, open(os.path.join(root, "research", "brief.json"), "w"), indent=1, ensure_ascii=False)
    L = ["# Task: write script.md (AGENT_REQUIRED)", "", f"Target: {b['target_words'][0]}-{b['target_words'][1]} spoken words ({MIN_S // 60}-{MAX_S // 60} minutes at {WPS} words/s). Verified-fact capacity: about {capacity} words.",
         "If capacity is below the target, write the honest shorter script and say so; padding and repetition fail validation.", "", "## Style"] + [f"- {s}" for s in STYLE]
    L += ["", "## Chapters (headings must match exactly: `## id: Title`)"]
    for c in sk:
        L.append(f"- `## {c['id']}: {c['title']}` - claims: {', '.join(c['claims']) or '(none; narrative/limits only)'}")
    L += ["", "## Claims you may use", *[f"- {i} [{v['tier']}/{v['confidence']}] {v['text']}" + (f" (word: {v['wording']!r})" if v["wording"] else "") for i, v in b["claims"].items()],
          "", "## Do NOT use (low confidence)", ", ".join(b["do_not_use"]) or "none", "",
          "When done run: `python3 .claude/skills/yt-script-agent/scriptagent.py validate --root productions/<slug>`"]
    os.makedirs(os.path.join(root, "tasks"), exist_ok=True)
    open(os.path.join(root, "tasks", "script.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    return b


def spoken_words(text):
    out = {}
    cur = None
    for line in text.splitlines():
        s = line.strip()
        m = CH_RE.match(s)
        if m:
            cur = m.group(1); out[cur] = []; continue
        if not s or s.startswith(("#", "[", ">", "---", "<!--")) or cur is None:
            continue
        out[cur] += TAG.sub("", s.replace("**", "")).split()
    return out


def repetition(words):
    """Share of 5-grams that repeat, and any sentence that appears twice (padding signals)."""
    w = [x.lower().strip(".,;:!?\"'") for x in words]
    grams = [tuple(w[i:i + 5]) for i in range(len(w) - 4)]
    c = collections.Counter(grams)
    rep = sum(v - 1 for v in c.values() if v > 1)
    return rep / max(1, len(grams)), [" ".join(g) for g, v in c.items() if v > 2][:3]


def validate(root):
    probs, warns = [], []
    p = os.path.join(root, "script.md")
    if not os.path.exists(p):
        return {"status": "needs_agent", "problems": ["script.md missing"]}
    text = open(p, encoding="utf-8").read()
    b = json.load(open(os.path.join(root, "research", "brief.json")))
    ch = spoken_words(text)
    want = [c["id"] for c in b["chapters"]]
    if list(ch) != want:
        probs.append(f"chapters {list(ch)} do not match the brief {want}")
    allw = [w for c in ch.values() for w in c]
    n = len(allw)
    secs = n / WPS
    if secs < MIN_S:
        (probs if not b["insufficient_facts"] else warns).append(f"{n} words = {secs:.0f}s, under 6 minutes" + (" (the verified facts do not carry more: INSUFFICIENT_FACTS)" if b["insufficient_facts"] else ""))
    if secs > MAX_S + 30:
        probs.append(f"{n} words = {secs:.0f}s, over 9 minutes")
    if "hook" in ch and len(ch["hook"]) > 70:
        probs.append(f"hook is {len(ch['hook'])} words (max 70)")
    rate, reps = repetition(allw)
    if rate > 0.03:
        probs.append(f"repetition {rate:.1%} of 5-grams (padding?): {reps}")
    used = set(re.findall(r"\{(C\d+(?:\s*,\s*C\d+)*)\}", text))
    used = {x.strip() for u in used for x in u.split(",")}
    cl = json.load(open(os.path.join(root, "claims.json")))["claims"]
    for c in cl:
        if c.get("must_cover") and c["id"] not in used:
            probs.append(f"must-cover claim {c['id']} is not used")
    for cid in b["do_not_use"]:
        if cid in used:
            probs.append(f"{cid} is low confidence and must not be used")
    pr = subprocess.run([sys.executable, FACTS, "--claims", "claims.json", "--script", "script.md", "--root", "."], cwd=root, capture_output=True, text=True)
    try:
        f = json.loads(pr.stdout)
        probs += f.get("problems", [])
    except ValueError:
        probs.append("yt-facts failed: " + (pr.stderr or pr.stdout)[:200])
    return {"status": "blocked" if probs else "ok", "words": n, "seconds": round(secs), "minutes": round(secs / 60, 1), "chapters": {k: len(v) for k, v in ch.items()},
            "repetition": round(rate, 4), "claims_used": sorted(used), "problems": probs, "warnings": warns}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["brief", "validate"])
    ap.add_argument("--root", default=".")
    a = ap.parse_args(argv)
    try:
        r = brief(a.root) if a.cmd == "brief" else validate(a.root)
        if a.cmd == "brief":
            r = {"status": "ok", "chapters": [c["id"] for c in r["chapters"]], "target_words": r["target_words"], "capacity_words": r["factual_capacity_words"], "insufficient_facts": r["insufficient_facts"]}
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return 0 if r["status"] == "ok" else 1
    except (OSError, KeyError, ValueError) as e:
        print(json.dumps({"status": "error", "error": f"{type(e).__name__}: {e}"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
