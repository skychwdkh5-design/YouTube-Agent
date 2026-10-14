#!/usr/bin/env python3
"""effects.py - the library of verified visual effects, so nobody rebuilds one that already exists.

    python3 tools/memory/effects.py search WORDS...      # what exists for this idea? (check BEFORE writing any effect code)
    python3 tools/memory/effects.py for CONTENT_TYPE     # effects usable for: locate, number, mechanism, change_over_time, ...
    python3 tools/memory/effects.py validate             # every code/test reference must exist
    python3 tools/memory/effects.py reuse-check PATH     # would writing this new file duplicate an effect? (reads the file)

knowledge/effects.json lists what the renderers REALLY do (status built / episode_only / not_built). The storyboard
generator only chooses `built` effects whose renderer is `yt-render-v3*`; `not_built` entries are the "do not claim" list.
The PreToolUse guard calls reuse_check() for every new code file written under orbitalatlas/, tools/ and productions/*/.
Writing a genuinely new variant is allowed: add the line `# effect-reuse-checked: <why it differs>` to the file.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG = os.path.join(ROOT, "knowledge", "effects.json")
STATUSES = ("built", "episode_only", "not_built")
GENERIC = {"label", "cut", "video", "step", "graphic", "bed", "clip", "pan", "push", "fill", "camera", "pin", "arrow", "flip", "wipe", "year",
           "number", "stat", "tag", "travel", "widen", "mask", "outline", "insert", "reveal", "drift"}
MARKER = "effect-reuse-checked:"


def load(path=CATALOG):
    with open(path, encoding="utf-8") as f: d = json.load(f)
    if d.get("schema") != "orbitalatlas-effects/1": raise ValueError("bad effects schema")
    return d


def validate(data=None):
    data = data or load()
    problems, seen = [], set()
    for e in data["entries"]:
        i = e.get("id", "?")
        if i in seen: problems.append(f"{i}: duplicate id")
        seen.add(i)
        for k in ("id", "kind", "renderer", "status", "what", "keywords", "refs"):
            if k not in e: problems.append(f"{i}: missing {k}")
        if e.get("status") not in STATUSES: problems.append(f"{i}: status must be one of {STATUSES}")
        for grp in (e.get("refs") or {}).values():
            for p in grp:
                if not os.path.exists(os.path.join(ROOT, p)): problems.append(f"{i}: reference not found: {p}")
    return {"ok": not problems, "entries": len(data["entries"]), "problems": problems}


def _tok(s):
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    return re.findall(r"[a-z0-9]+", s.lower())


def search(words, data=None):
    q = set(_tok(" ".join(words)))
    out = []
    for e in (data or load())["entries"]:
        bag = set(_tok(e["id"] + " " + e["what"] + " " + " ".join(e["keywords"]) + " " + " ".join(e.get("use_for", []))))
        n = len(q & bag)
        if n: out.append((n, e))
    out.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [{"id": e["id"], "status": e["status"], "renderer": e["renderer"], "what": e["what"], "limits": e.get("limits", ""), "refs": e["refs"], "score": n} for n, e in out]


def for_content(ctype, data=None):
    return [e for e in (data or load())["entries"] if e["status"] == "built" and e["renderer"].startswith("yt-render-v3") and ctype in e.get("use_for", [])]


def reuse_check(path, content, data=None):
    """Return a list of existing effects this NEW code file would probably duplicate (empty = fine)."""
    if MARKER in content: return []
    names = " ".join(_tok(os.path.splitext(os.path.basename(path))[0]) + [t for m in re.findall(r"^\s*(?:def|class)\s+(\w+)", content, re.M) for t in _tok(m)])
    hay = " " + " ".join(_tok(names)) + " "
    hits = []
    for e in (data or load())["entries"]:
        if e["status"] == "not_built": continue
        for kw in e["keywords"]:
            toks = _tok(kw)
            if len(toks) == 1 and toks[0] in GENERIC: continue
            if all(f" {t} " in hay or f" {t}s " in hay for t in toks):
                hits.append({"id": e["id"], "status": e["status"], "what": e["what"], "refs": e["refs"], "matched": kw}); break
    return hits


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return 0
    try:
        if a[0] == "search": print(json.dumps(search(a[1:]), indent=1, ensure_ascii=False)); return 0
        if a[0] == "for": print(json.dumps([e["id"] for e in for_content(a[1])], indent=1)); return 0
        if a[0] == "validate":
            r = validate(); print(json.dumps(r, indent=1)); return 0 if r["ok"] else 1
        if a[0] == "reuse-check":
            with open(a[1], encoding="utf-8") as f: hits = reuse_check(a[1], f.read())
            print(json.dumps(hits, indent=1, ensure_ascii=False)); return 1 if hits else 0
    except (OSError, ValueError, IndexError) as x:
        print(json.dumps({"ok": False, "error": str(x)})); return 2
    print(json.dumps({"ok": False, "error": "unknown command"})); return 2


if __name__ == "__main__":
    sys.exit(main())
