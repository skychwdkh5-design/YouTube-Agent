#!/usr/bin/env python3
"""title.py - lint a YouTube title and thumbnail pairing before you publish it.

    python3 title.py --title "..." --thumb "AI RAN IT"
    python3 title.py titles.txt            # one per line, ranked
    python3 title.py --title "..." --json
    python3 title.py --profile geo titles.txt    # geography: place names count as names

GEO PROFILE. In geography the name IS the specific: "Minnesota", "Canada" and "Point Roberts" do the
job a number does elsewhere. With --profile geo a place from places.txt satisfies the
"number, date or name" check, and dotted abbreviations (U.S., D.C., U.K.) are not counted as
shouting. Without the flag every result is exactly what it always was.

The pairing is the unit, not the title. A title that repeats the thumbnail text wastes half the
click surface, and that is the single most common mistake this checks for.

Length: YouTube truncates around 60 characters on desktop search and around 40 on a mobile home
feed. Both limits are reported because they are different failures - a desktop truncation loses the
tail, a mobile one can lose the subject.
"""
import json, re, sys, os

DESKTOP, MOBILE, HARD = 60, 40, 100
VAGUE = {"amazing","incredible","insane","crazy","huge","massive","ultimate","best","powerful",
         "secret","revolutionary","mindblowing","epic","perfect","complete","everything"}
STOP = {"the","a","an","of","for","to","in","on","and","or","is","are","with","your","you","my","i",
        "this","that","it","how","what","why"}

def words(t): return re.findall(r"[a-z0-9']+", t.lower())

HERE = os.path.dirname(os.path.abspath(__file__))

def load_places(path=os.path.join(HERE, "places.txt")):
    if not os.path.exists(path): return []
    return [l.strip() for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]

def find_places(t, places):
    hits, text = [], t
    # longest names first, and blank each match out, so "New Mexico" is not also read as "Mexico"
    for p in sorted(places, key=len, reverse=True):
        # abbreviations (US, UK, U.S.) match case-sensitively so "us" the pronoun is not a country
        exact = p.isupper() or "." in p
        pat = r"(?<![\w.])" + re.escape(p) + r"(?![\w])"
        m = re.search(pat, text, 0 if exact else re.I)
        if m:
            hits.append(p)
            text = re.sub(pat, lambda x: " " * len(x.group(0)), text, flags=0 if exact else re.I)
    return hits

def check(title, thumb=None, profile=None):
    t = title.strip()
    geo = profile == "geo"
    places = find_places(t, load_places()) if geo else []
    n = len(t)
    issues, good = [], []
    if n > HARD: issues.append(("length", f"{n} characters - YouTube's hard limit is {HARD}"))
    elif n > DESKTOP: issues.append(("length", f"{n} characters - desktop search cuts near {DESKTOP}"))
    else: good.append(f"{n} characters, inside the {DESKTOP}-character desktop cut")
    if n > MOBILE:
        head = t[:MOBILE].rsplit(" ", 1)[0]
        issues.append(("mobile", f'a mobile feed shows about "{head}..." - check the subject survives'))
    caps = [w for w in t.split() if len(w) > 2 and w.isupper() and not (geo and "." in w)]
    if len(caps) > 2: issues.append(("shouting", f"{len(caps)} all-caps words - two is the ceiling before it reads as spam"))
    elif caps: good.append(f"{len(caps)} all-caps word for emphasis")
    v = [w for w in words(t) if w in VAGUE]
    if v: issues.append(("vague", f"{', '.join(sorted(set(v)))} - swap for a number, a name or a date"))
    nums = re.findall(r"\d[\d,.]*%?", t)
    if nums: good.append(f"carries a concrete figure ({', '.join(nums[:3])})")
    if places: good.append(f"names a place ({', '.join(places[:3])})")
    if not nums and not places:
        issues.append(("no-number", "no number, date or name - the most reliable single fix"))
    if t.endswith("?"): good.append("open question in the title")
    front = [w for w in words(t)[:3] if w not in STOP]
    if not front: issues.append(("front-load", "the first three words are all filler - move the subject forward"))
    if thumb:
        tw, hw = set(words(t)) - STOP, set(words(thumb)) - STOP
        shared = tw & hw
        if shared:
            issues.append(("duplicate", f"thumbnail repeats the title on {', '.join(sorted(shared))} - "
                                        "the thumbnail should say what the title does not"))
        else:
            good.append("thumbnail and title carry different words")
        if len(words(thumb)) > 4:
            issues.append(("thumb-length", f"{len(words(thumb))} words on the thumbnail - three is the ceiling at feed size"))
    score = max(0, min(100, 100 - 14 * len(issues) + 4 * len(good)))
    return {"title": t, "chars": n, "score": score, "issues": issues, "good": good}

def show(r):
    print(f'\n  "{r["title"]}"')
    print(f"  {r['chars']} chars   score {r['score']}/100")
    for k, m in r["issues"]: print(f"    x  {k:<12} {m}")
    for m in r["good"]:      print(f"    ok              {m}")

def main():
    a = sys.argv[1:]
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    profile = None
    if "--profile" in a:
        i = a.index("--profile"); profile = a[i + 1] if i + 1 < len(a) else None; del a[i:i + 2]
    thumb = a[a.index("--thumb") + 1] if "--thumb" in a else None
    if "--title" in a:
        rows = [check(a[a.index("--title") + 1], thumb, profile)]
    elif a and os.path.exists(a[0]):
        rows = [check(l, thumb, profile) for l in open(a[0]).read().splitlines() if l.strip()]
    else:
        print(__doc__); sys.exit(1)
    rows.sort(key=lambda r: -r["score"])
    if as_json: print(json.dumps(rows, indent=1)); return
    for r in rows: show(r)
    print()

if __name__ == "__main__":
    main()
