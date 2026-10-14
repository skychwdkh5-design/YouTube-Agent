"""Narration-to-visual mapping (the 'audiovisual synchronisation engine').

Input : the English narration as WORDS WITH TIMESTAMPS ([{'text','start','end'}]; provider timestamps or a verified alignment) and, optionally, a gazetteer
        of places the episode can actually show ({name: {...}} - from the geo stack, never guessed here).
Output: a reproducible plan (plain dict / JSON): tagged words, timed visual EVENTS, caption cards with a style per card and the timing source.

Rules (each is a deterministic function of the words; same input -> same plan):
  year          'In 1985' -> year label at the word                                      (kind year)
  number        large numbers, percentages, money, measures -> number typography         (kind number)
  place         a gazetteer name -> highlight + camera move toward it                    (kind place)
  route         'from X to Y' / 'across' with two places -> animated arrow               (kind route)
  comparison    'than', 'versus', 'compared with', 'before/after', 'then ... now' -> comparison visual   (kind comparison)
  emphasis      superlatives / extremes / negations ('largest', 'record', 'never', 'only') -> word emphasis in captions   (kind emphasis)
  revelation    a sentence opening with 'But/Yet/Then came/Until' or a colon -> stronger emphasis (impact caption, camera push)   (kind revelation)
  complex       a sentence with more than `complex_words` words or 3+ data items -> reduce clutter (kind simplify)
Density limit: at most `max_events_per_10s` non-caption events per sliding 10 s; lower-priority events are dropped and listed under `dropped`.
Nothing here invents facts: events carry the word that triggered them and the rule name."""
import re
from . import captions as C

PRIORITY = {"revelation": 6, "route": 5, "comparison": 5, "place": 4, "year": 4, "number": 3, "emphasis": 2, "simplify": 1}
EXTREMES = {"largest", "biggest", "smallest", "lowest", "highest", "deepest", "longest", "shortest", "record", "first", "last", "only", "never", "worst", "best",
            "most", "least", "entire", "completely", "massive", "enormous", "tiny", "unprecedented", "fastest", "driest", "wettest", "hottest", "coldest", "almost", "nearly"}
CHANGE = {"fallen", "shrunk", "shrinking", "drying", "dried", "vanished", "disappeared", "dropped", "collapsed", "split", "splits", "pulled", "retreated", "worsens", "dust"}
MONTHS = {"january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"}
UNITS = {"km", "kilometers", "kilometres", "miles", "mile", "feet", "foot", "meters", "metres", "acres", "percent", "million", "billion", "thousand", "trillion", "square", "cubic", "degrees", "tons", "people"}
COMPARE = {"than", "versus", "vs", "compared", "before", "after", "earlier", "later", "different", "same", "instead"}
REVEAL_OPEN = {"but", "yet", "until", "suddenly", "then", "however"}
MOTION = {"flows", "flowed", "flowing", "moved", "moves", "travels", "travelled", "traveled", "crosses", "crossed", "across", "from", "through", "toward", "towards"}


def _norm(t): return re.sub(r"[^\w']", "", t.lower())


def tag_words(words, places=None):
    """return copies of the words with 'kind' (year/number/place/None) and 'emph' (bool) set; places: {name: info} (multi-word names allowed)."""
    out = [dict(w) for w in words]; norms = [_norm(w["text"]) for w in out]; places = places or {}
    names = sorted(((n.lower().split(), n) for n in places), key=lambda x: -len(x[0]))
    i = 0
    while i < len(out):
        hit = None
        for toks, name in names:
            if norms[i:i + len(toks)] == [re.sub(r"[^\w']", "", x) for x in toks]: hit = (len(toks), name); break
        if hit:
            for j in range(i, i + hit[0]): out[j]["kind"] = "place"; out[j]["place"] = hit[1]
            i += hit[0]; continue
        w = out[i]["text"]
        if C.is_year(w): out[i]["kind"] = "year"
        elif C.is_number(w) or (i + 1 < len(out) and re.match(r"^\d", C.clean(w) or "x") and norms[i + 1] in UNITS): out[i]["kind"] = "number"
        elif norms[i] in MONTHS and i + 1 < len(out) and C.is_year(out[i + 1]["text"]): out[i]["kind"] = "year"
        out[i]["emph"] = norms[i] in EXTREMES or norms[i] in CHANGE
        i += 1
    return out


def sentences(words):
    """split into sentences by terminal punctuation: list of index ranges (i0, i1 exclusive)."""
    out, s = [], 0
    for i, w in enumerate(words):
        if re.search(r"[.!?]$", w["text"]) or i == len(words) - 1: out.append((s, i + 1)); s = i + 1
    return out


def plan(words, places=None, mode="long", source="provider", complex_words=24, max_events_per_10s=4, complexity=None, min_gap=0.8):
    """build the plan. `source` must say where the timestamps come from ('provider' | 'alignment' | 'estimated' | 'simulated'); only the first two are frame-accurate."""
    tw = tag_words(words, places); ev = []; dropped = []
    def add(kind, i, **kw): ev.append(dict(kind=kind, t=round(tw[i]["start"], 3), word=i, text=tw[i]["text"], priority=PRIORITY[kind], **kw))
    for a, b in sentences(tw):
        toks = [_norm(w["text"]) for w in tw[a:b]]; sent = " ".join(w["text"] for w in tw[a:b])
        data = [i for i in range(a, b) if tw[i].get("kind") in ("year", "number") and not (i > a and tw[i]["kind"] == "year" and _norm(tw[i - 1]["text"]) in MONTHS)]   # 'July 2022' is ONE date
        pl = [i for i in range(a, b) if tw[i].get("kind") == "place" and (i == a or tw[i - 1].get("place") != tw[i].get("place"))]
        if toks and (toks[0] in REVEAL_OPEN and (toks[0] != "then" or "came" in toks[:3])) or ":" in sent or " — " in sent:
            add("revelation", a, rule="sentence opens with a turn")
        if b - a > complex_words or len(data) >= 3: add("simplify", a, rule=f"{b - a} words, {len(data)} data items")
        for i in data: add(tw[i]["kind"], i, rule=tw[i]["kind"])
        for i in pl: add("place", i, place=tw[i]["place"], rule="gazetteer")
        if len(pl) >= 2 and any(t in MOTION for t in toks):
            add("route", pl[0], to=tw[pl[1]]["place"], frm=tw[pl[0]]["place"], rule="two places with a motion word")
        for i in range(a, b):
            n = toks[i - a]
            if n in COMPARE or (n == "then" and "now" in toks[i - a:]): add("comparison", i, rule=f"'{n}'"); break
        for i in range(a, b):
            if tw[i].get("emph"): add("emphasis", i, rule="extreme / change word")
    ev.sort(key=lambda e: (e["t"], -e["priority"], e["word"]))
    kept = []
    for e in ev:                                         # density limit + per-kind minimum gap, highest priority wins inside a window
        if e["kind"] == "emphasis" or e["kind"] == "simplify": kept.append(e); continue
        close = [k for k in kept if k["kind"] not in ("emphasis", "simplify") and abs(k["t"] - e["t"]) < 10.0]
        if len(close) >= max_events_per_10s:
            lowest = min(close, key=lambda k: k["priority"])
            if lowest["priority"] < e["priority"]: kept.remove(lowest); dropped.append(dict(lowest, why="density limit")); kept.append(e)
            else: dropped.append(dict(e, why="density limit"))
            continue
        if any(k["kind"] == e["kind"] and e["t"] - k["t"] < min_gap and k["kind"] != "year" for k in kept):
            dropped.append(dict(e, why="too close to the same kind")); continue
        kept.append(e)
    kept.sort(key=lambda e: (e["t"], -e["priority"]))
    cards = C.make_cards(tw)
    impact = {ci for ci, c in enumerate(cards) if any(e["kind"] == "revelation" and c["words"][0]["start"] - 2e-3 <= e["t"] <= c["t1"] for e in kept)}
    styles = C.plan_styles(cards, mode, complexity, impact)
    return dict(schema="orbitalatlas-plan/1", mode=mode, timing_source=source, frame_accurate=source in ("provider", "alignment"),
                words=tw, events=kept, dropped=dropped, cards=[dict(t0=c["t0"], t1=c["t1"], text=" ".join(w["text"] for w in c["words"]), style=s) for c, s in zip(cards, styles)],
                styles="".join(styles), n_cards=len(cards))
