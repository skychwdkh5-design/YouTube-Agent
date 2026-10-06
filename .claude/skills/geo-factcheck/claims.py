#!/usr/bin/env python3
"""claims.py - the fact-check gate. A script does not move on until this exits 0.

    python3 claims.py --claims claims.md                      # GATE 1: is the ledger itself sound?
    python3 claims.py --claims claims.md --script script.md   # GATE 2: is every claim in the script verified?
    python3 claims.py --claims claims.md --script script.md --json

THE LEDGER (claims.md) is a markdown table, one row per factual claim:

    | ID | Claim | Type | Source | URL | Accessed | Tier | Status | Final wording |

  - Several sources go in one cell separated by " ; " (Source, URL and Tier line up by position).
  - Status is one of VERIFIED, SOFTENED, UNVERIFIED, CONFLICT, CUT. Only VERIFIED and SOFTENED pass.
  - Tier 1 = primary/official (Census, USGS, a statute, a treaty text, a national statistics office),
    Tier 2 = reputable secondary (peer-reviewed, major reference, major newsroom), Tier 3 = a lead only
    (Wikipedia, forums, YouTube, blogs). A claim cannot be verified on Tier 3 alone.

THE SCRIPT tags every factual sentence with its ledger ID: "...only by driving through Canada [C3]."
A sentence that carries a number, a year, a measurement, a ranking or a superlative and has no tag
fails the gate. A sentence that trips the detector but is not a factual claim ("the first thing you
notice") is marked [NC] - reviewed, not a claim. If the script has lines starting "VO:", only those
are read; otherwise every non-heading line is. Anything in [brackets] other than the tags is a
visual note and is ignored.

Exit code 0 = PASS, 1 = FAIL. Warnings never fail the gate; they are for the human to read.
"""
import datetime, json, re, sys
from urllib.parse import urlparse

PASS_STATUS = {"VERIFIED", "SOFTENED"}
ALL_STATUS = PASS_STATUS | {"UNVERIFIED", "CONFLICT", "CUT"}
TERTIARY = ("wikipedia.org", "wikimedia.org", "reddit.com", "quora.com", "fandom.com", "youtube.com",
            "youtu.be", "tiktok.com", "medium.com", "blogspot.", "wordpress.com", "pinterest.",
            "facebook.com", "x.com", "twitter.com", "instagram.com")
TIME_SENSITIVE = {"population", "statistic", "ranking"}
SUPERLATIVE = re.compile(
    r"\b(largest|smallest|biggest|longest|shortest|highest|lowest|oldest|newest|youngest|tallest|"
    r"deepest|widest|narrowest|northernmost|southernmost|easternmost|westernmost|hottest|coldest|"
    r"driest|wettest|densest|emptiest|remotest|most (?:populous|remote|isolated|densely|visited)|"
    r"least (?:populous|densely|visited)|fastest[- ]growing|only|the first|first to|the last|"
    r"last remaining|record|ranks?|ranked|number one|top (?:ten|five|three|\d+))\b", re.I)
NUMWORD = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)"
UNIT = r"(?:miles?|kilometers?|km|feet|foot|meters?|yards?|acres?|square|sq|hectares?|people|residents|inhabitants|years?|centuries|decades|countries|states|islands|degrees|percent|times)"
NUMERIC = [
    re.compile(r"\d"),
    re.compile(r"\b(hundred|thousand|million|billion|trillion|percent|dozens?|half|a third|a quarter|majority)\b", re.I),
    re.compile(r"\b" + NUMWORD + r"\b(?:[\s-]\w+){0,2}?\s" + UNIT + r"\b", re.I),
    re.compile(r"\b(seventeen|eighteen|nineteen|sixteen) (hundred|\w+ty|\w+-\w+)\b", re.I),
]
TAG = re.compile(r"\[(C\d+|NC)\]")

def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]

def parse_ledger(path):
    rows, header = [], None
    for line in open(path, encoding="utf-8"):
        if not line.strip().startswith("|"):
            if header is not None: break      # only the first table is the data; later tables are notes
            continue
        c = cells(line)
        if all(re.fullmatch(r":?-{2,}:?", x) for x in c if x): continue
        if header is None:
            header = [h.lower() for h in c]; continue
        r = dict(zip(header, c + [""] * (len(header) - len(c))))
        if r.get("id"): rows.append(r)
    return rows

def split(v): return [x.strip() for x in re.split(r"\s;\s|;", v or "") if x.strip()]

def domain(u):
    try: return urlparse(u).netloc.lower().removeprefix("www.")
    except Exception: return ""

def check_ledger(rows, today):
    fails, warns, seen = [], [], set()
    for r in rows:
        cid, status = r.get("id", ""), (r.get("status") or "").upper()
        where = f"{cid}"
        if not re.fullmatch(r"C\d+", cid): fails.append((where, f"ID must look like C1, C2 ... (got '{cid}')"))
        if cid in seen: fails.append((where, "duplicate ID"))
        seen.add(cid)
        if status not in ALL_STATUS:
            fails.append((where, f"status '{status or '-'}' is not one of {', '.join(sorted(ALL_STATUS))}")); continue
        if status not in PASS_STATUS: continue
        urls = [u for u in split(r.get("url")) if u.startswith("http")]
        tiers = [int(t) for t in re.findall(r"\d", r.get("tier", ""))]
        ctype = (r.get("type") or "").lower()
        text = f"{r.get('claim','')} {r.get('final wording','')}"
        if not urls: fails.append((where, "verified with no source URL")); continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r.get("accessed", "")):
            fails.append((where, "Accessed must be a YYYY-MM-DD date - when the source was read"))
        if not tiers: fails.append((where, "no Tier given for the source(s)"))
        elif min(tiers) > 2: fails.append((where, "Tier 3 only - a lead is not a source. Find the primary"))
        if all(any(t in domain(u) for t in TERTIARY) for u in urls):
            fails.append((where, f"every URL is a tertiary site ({', '.join(sorted({domain(u) for u in urls}))})"))
        if ctype in {"superlative", "ranking"} or SUPERLATIVE.search(text):
            if len({domain(u) for u in urls}) < 2:
                fails.append((where, "superlative/ranking/'only' claim needs two independent sources (two domains)"))
        if ctype in TIME_SENSITIVE and not re.search(r"\b(1[5-9]|20)\d{2}\b|as of", text, re.I):
            warns.append((where, f"{ctype} claim with no year in its wording - say 'as of the 2020 Census' etc."))
        if ctype in TIME_SENSITIVE and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r.get("accessed", "")):
            age = (today - datetime.date.fromisoformat(r["accessed"])).days
            if age > 365: warns.append((where, f"source read {age} days ago - re-check the figure is current"))
        if status == "SOFTENED" and not r.get("final wording"):
            fails.append((where, "SOFTENED needs the Final wording that the script must use"))
    return fails, warns

def narration(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    vo = [l for l in lines if l.strip().upper().startswith("VO:")]
    use = [l.strip()[3:] for l in vo] if vo else [l for l in lines if l.strip() and not l.lstrip().startswith(("#", ">", "---", "|"))]
    out = []
    for l in use:
        l = re.sub(r"\[(?!(?:C\d+|NC)\])[^\]]*\]", " ", l)           # visual notes are not narration
        l = re.sub(r"\*\*|__|`", "", l)
        # a tag written after the full stop belongs to the sentence before it
        l = re.sub(r"([.!?])\s*((?:\[(?:C\d+|NC)\]\s*)+)", lambda m: " " + m.group(2).strip() + m.group(1) + " ", l)
        out.append(l)
    return " ".join(out)

def check_script(path, rows):
    fails, warns = [], []
    by = {r["id"]: r for r in rows}
    text = narration(path)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    used = set()
    for s in sentences:
        tags = TAG.findall(s)
        bare = TAG.sub("", s).strip()
        used.update(t for t in tags if t != "NC")
        for t in tags:
            if t == "NC": continue
            if t not in by: fails.append((t, f'tag not in the ledger: "{bare[:70]}"'))
            elif (by[t].get("status") or "").upper() not in PASS_STATUS:
                fails.append((t, f'{by[t].get("status","?").upper()} claim is still in the script: "{bare[:70]}"'))
        if tags: continue
        hit = SUPERLATIVE.search(bare) or next((m for p in NUMERIC for m in [p.search(bare)] if m), None)
        if hit: fails.append(("UNTAGGED", f'"{hit.group(0)}" in: "{bare[:90]}" - tag it [C#] or mark [NC]'))
    for cid, r in by.items():
        if (r.get("status") or "").upper() in PASS_STATUS and cid not in used:
            warns.append((cid, "verified but not used in the script - fine, or a line went missing"))
    return fails, warns, len(sentences)

def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    get = lambda k: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None
    ledger, script = get("--claims"), get("--script")
    if not ledger: print(__doc__); sys.exit(2)
    rows = parse_ledger(ledger)
    fails, warns = check_ledger(rows, datetime.date.today())
    n_sent = None
    if script:
        f2, w2, n_sent = check_script(script, rows)
        fails += f2; warns += w2
    counts = {}
    for r in rows: counts[(r.get("status") or "-").upper()] = counts.get((r.get("status") or "-").upper(), 0) + 1
    usable = sum(n for k, n in counts.items() if k in PASS_STATUS)
    if rows and usable < len(rows):
        # PASS means the ledger is well-formed, not that the facts are checked. Say so.
        warns.append(("LEDGER", f"{usable} of {len(rows)} claims are VERIFIED/SOFTENED - a script may use only those"))
    result = {"gate": "PASS" if not fails else "FAIL", "claims": len(rows), "status_counts": counts,
              "sentences_checked": n_sent, "fails": fails, "warnings": warns}
    if as_json:
        print(json.dumps(result, indent=1))
    else:
        print(f"\n  ledger {ledger}: {len(rows)} claims  " + "  ".join(f"{k} {v}" for k, v in sorted(counts.items())))
        if script: print(f"  script {script}: {n_sent} sentences checked")
        for w, m in fails: print(f"    FAIL  {w:<9} {m}")
        for w, m in warns: print(f"    warn  {w:<9} {m}")
        print(f"\n  GATE: {result['gate']}" + ("" if not fails else f"  ({len(fails)} to fix before this moves on)") + "\n")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
