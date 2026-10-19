#!/usr/bin/env python3
"""storyboard.py - generate an editable timeline.json (yt-render v3, profile long) from a script, word timings and an asset manifest.

    python3 tools/autopilot/storyboard.py plan SLUG [--timings provider|estimated] [--no-graphics]
    python3 tools/autopilot/storyboard.py preview SLUG [--start S] [--end E] [--confirm]     # short silent proof render (free)

Inputs, all in productions/<slug>/:
  script.md                  plain paragraphs (one paragraph = one beat). Bracketed directions are never spoken and may carry hints:
                             [VIS: asset=mead_2022 label="LAKE MEAD" family=reservoir claims=C3 steps="a|b|c" type=number]
  voice/narration.voice.json provider word timings (yt-voice/1). Without it, --timings estimated builds a clearly flagged ESTIMATE
                             (2.38 words/s) - good for a proof, never for a release (timeline.meta.timing says so)
  assets/manifest.json       {"assets": [{id, kind: still|video, src, credit, source_url, license, retrieved, image_date, tags[], place, focus[x,y]}]}
  story/claims.json          optional; numbers shown as graphics need a verified claim with a source
Outputs: timeline.json, grid.json (dummy grid - needed by the renderer, unused by stills/graphics), story/storyboard.plan.json
(every decision, its score and the alternatives), story/storyboard.md (human-readable), graphics/ (yt-graphics specs + PNGs).

What it does NOT do (and says so in the plan): it never invents an asset, a number or a source. A scene without a usable
picture is reported in `gaps` and shown with the best related asset, marked `reused`. It only uses effects that the renderer
really has (knowledge/effects.json, status built, renderer yt-render-v3*). Geographic camera shots need a yt-geo stack and are
not generated here.
"""
import difflib, importlib.util, json, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILLS = os.path.join(ROOT, ".claude", "skills")
sys.path.insert(0, os.path.join(ROOT, "tools", "memory"))
import effects  # noqa: E402

FPS = 30
W, H = 1920, 1080
WPS = 2.38                      # words per second of the channel narrator (EP001 1778/747 s, EP002 1225/515 s)
MIN_SCENE_S, MAX_SCENE_S, HOLD_S, HOOK_BEAT_S = 4.0, 8.0, 8.0, 3.6
LABEL_MAX = 28
STILL_MAX_UPSCALE = 4.0
DUMMY_GRID = {"schema": "yt-geo-stack/1", "epsg": 32611, "x0": 0.0, "y_top": 0.0, "pixel_m": 30.0, "width": W, "height": H}
CALLOUT_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(percent|%|square miles|square kilometers|miles|kilometers|km|hectares|feet|meters|degrees|years|million|billion|islands|people)", re.I)
YEAR_RE = re.compile(r"\b(1[89]\d\d|20\d\d)\b")
CHANGE_RE = re.compile(r"\b(before|after|then|now|since|compare|compared|between|grew|shrank|shrunk|lost|gained|doubled|fell|rose|declined|changed)\b", re.I)


def q(t): return round(t * FPS) / FPS


def norm(w): return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def _voice():
    spec = importlib.util.spec_from_file_location("yt_voice_sb", os.path.join(SKILLS, "yt-voice", "voice.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError):
        return default


# ------------------------------------------------------------------------------------------------ script, words
HINT_RE = re.compile(r"\[VIS:\s*(.*?)\]", re.S)
KV_RE = re.compile(r'(\w+)=("([^"]*)"|\S+)')


def parse_script(raw):
    """-> [{text, hints}] one per non-empty paragraph line that has spoken text. Hints come from [VIS: k=v ...] on the line."""
    spoken = _voice().spoken_text
    blocks = []
    pending = {}
    for line in raw.splitlines():
        hints = {}
        for m in HINT_RE.finditer(line):
            for k, v, vq in KV_RE.findall(m.group(1)):
                hints[k] = vq if v.startswith('"') else v
        text = spoken(line, False)[0].strip() if line.strip() else ""
        if not text:
            pending.update(hints)                  # a direction line on its own applies to the next paragraph
            continue
        blocks.append({"text": text, "hints": {**pending, **hints}})
        pending = {}
    return blocks


def estimate_words(blocks):
    words, t = [], 0.0
    for b in blocks:
        for tok in b["text"].split():
            d = max(0.12, len(re.sub(r"\W", "", tok)) * 0.055 + 0.08)
            words.append({"text": tok, "start": round(t, 3), "end": round(t + d, 3)})
            t += d + (0.28 if tok[-1:] in ".?!" else 0.12 if tok[-1:] in ",;:" else 0.0)
    return words


def align(blocks, words):
    """Give every block its word range [i0, i1). Cumulative token counts; on a mismatch, resync with difflib."""
    total = sum(len(b["text"].split()) for b in blocks)
    if total == len(words):
        i = 0
        for b in blocks:
            n = len(b["text"].split()); b["w0"], b["w1"] = i, i + n; i += n
        return {"method": "token-count", "exact": True}
    a = [norm(t) for b in blocks for t in b["text"].split()]
    c = [norm(w["text"]) for w in words]
    sm = difflib.SequenceMatcher(None, a, c, autojunk=False)
    mapping = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1): mapping[i1 + k] = j1 + k
    if len(mapping) < 0.9 * len(a):
        raise ValueError(f"script and narration words differ too much ({len(mapping)}/{len(a)} words match); the script changed after the voice")
    i = 0
    last = 0
    for b in blocks:
        n = len(b["text"].split())
        idx = [mapping[k] for k in range(i, i + n) if k in mapping]
        b["w0"] = idx[0] if idx else last
        b["w1"] = (idx[-1] + 1) if idx else b["w0"]
        last = b["w1"]; i += n
    return {"method": "difflib-resync", "exact": False, "matched": len(mapping), "of": len(a)}


# ------------------------------------------------------------------------------------------------ scenes
def first_sentence(text):
    m = re.match(r"(.+?[.!?])(\s|$)", text.strip())
    return m.group(1) if m else text.strip()


def cut_points(words, w0, w1, fine):
    """Word indices (inside (w0, w1)) where a new sentence (or, if fine, clause) starts."""
    ends = ".!?" if not fine else ".!?,;:"
    return [i + 1 for i in range(w0, w1 - 1) if words[i]["text"][-1:] in ends or (fine and words[i]["text"].endswith("\u2014"))]


def split_scene(sc, words, max_s, min_part_s, fine, video_ids=()):
    """Recursively cut a scene at the boundary nearest its middle until every part is <= max_s (parts stay >= min_part_s)."""
    t0, t1 = words[sc["w0"]]["start"], words[sc["w1"] - 1]["end"]
    if t1 - t0 <= max_s or sc["hints"].get("steps") or sc["hints"].get("asset") in video_ids: return [sc]
    best = None
    for i in cut_points(words, sc["w0"], sc["w1"], fine):
        a_, b_ = words[i - 1]["end"] - t0, t1 - words[i]["start"]
        if a_ < min_part_s or b_ < min_part_s: continue
        d = abs(a_ - b_)
        if best is None or d < best[0]: best = (d, i)
    if best is None: return [sc]
    i = best[1]
    toks = sc["text"].split()
    k = i - sc["w0"]
    left = dict(sc, text=" ".join(toks[:k]), w1=i)
    right = dict(sc, text=" ".join(toks[k:]), w0=i, hints={x: y for x, y in sc["hints"].items() if x in ("family", "asset", "claims")})
    return split_scene(left, words, max_s, min_part_s, fine, video_ids) + split_scene(right, words, max_s, min_part_s, fine, video_ids)


def build_scenes(blocks, words, video_ids=()):
    """Paragraphs -> scenes. Short paragraphs merge forward; scenes over 8 s are cut at sentence ends; the hook (first 10 s) is cut at clause ends into ~3.4 s beats."""
    scenes, cur = [], None
    for b in blocks:
        u = {"text": b["text"], "hints": dict(b["hints"]), "w0": b["w0"], "w1": b["w1"]}
        if cur and (words[cur["w1"] - 1]["end"] - words[cur["w0"]]["start"] < MIN_SCENE_S) and not u["hints"].get("break") and not cur["hints"]:
            cur["text"] += " " + u["text"]; cur["w1"] = u["w1"]; cur["hints"].update(u["hints"]); continue
        if cur: scenes.append(cur)
        cur = u
    if cur: scenes.append(cur)
    out = []
    for sc in scenes:
        if words[sc["w0"]]["start"] < 10.0:
            out += split_scene(sc, words, HOOK_BEAT_S, 1.6, True, video_ids)
        else:
            out += split_scene(sc, words, MAX_SCENE_S, 3.0, False, video_ids)
    for i, s in enumerate(out, 1):
        s["id"] = f"sc{i:02d}"
        s["start"] = q(words[s["w0"]]["start"]) if i > 1 else 0.0
        s["sent_starts"] = [s["w0"]] + cut_points(words, s["w0"], s["w1"], False)
        s["sents"] = [first_sentence(s["text"])]
    for a, b in zip(out, out[1:]): a["end"] = b["start"]
    return out


def classify(scene):
    t = scene["text"]
    kinds = []
    years = set(YEAR_RE.findall(t))
    if len(years) >= 2 or (years and CHANGE_RE.search(t)): kinds.append("change_over_time")
    if CALLOUT_RE.search(t): kinds.append("number")
    if scene["hints"].get("steps"): kinds.append("mechanism")
    if scene["hints"].get("type"): kinds.insert(0, scene["hints"]["type"])
    return kinds or ["establish_place"]


# ------------------------------------------------------------------------------------------------ assets
def load_manifest(prod):
    m = _json(os.path.join(prod, "assets", "manifest.json"), {"assets": []})
    from PIL import Image
    out = []
    for a in m.get("assets", []):
        a = dict(a)
        p = os.path.join(prod, a["src"])
        a["exists"] = os.path.exists(p)
        if a["exists"] and a.get("kind", "still") == "still":
            try:
                with Image.open(p) as im: a["size"] = list(im.size)
            except OSError:
                a["exists"] = False
        a["tags"] = [t.lower() for t in a.get("tags", [])] + ([a["place"].lower()] if a.get("place") else [])
        out.append(a)
    return out


def relevance(scene, asset):
    text = scene["text"].lower()
    n = 0.0
    words_in_text = set(re.findall(r"[a-z0-9]+", text))
    for t in asset["tags"]:
        if not t: continue
        if re.search(r"\b" + re.escape(t) + r"\b", text): n += 1.0 + 0.3 * len(t.split()); continue
        toks = [x for x in re.findall(r"[a-z0-9]+", t) if x not in ("the", "of", "and", "in")]
        if len(toks) >= 2 and sum(x in words_in_text for x in toks) / len(toks) >= 0.6: n += 0.8      # partial multi-word match, e.g. "colorado river"
    for y in asset.get("years", []) + [str(asset.get("image_date", ""))[:4]]:
        if y and str(y) in text: n += 0.5
    if scene["hints"].get("asset") == asset["id"]: n += 10
    return n


def year_gap(scene, asset):
    """Years the narration names vs the years the picture shows: -> (smallest distance in years over the named years, or None).
    A video that spans 1984-2023 covers every year inside that range; a still covers its own year."""
    named = [int(y) for y in YEAR_RE.findall(scene["text"])]
    ay = [int(y) for y in asset.get("years", []) if str(y).isdigit()]
    if not named or not ay: return None
    lo, hi = min(ay), max(ay)
    if asset.get("kind", "still") == "video" and len(ay) >= 2:
        return max(0, max(lo - y if y < lo else y - hi if y > hi else 0 for y in named))
    return max(min(abs(y - a) for a in ay) for y in named)


def fit_view(asset, cx, cy, wf):
    """A 16:9 window of width fraction wf at (cx, cy), moved inside the image and kept under the upscale limit."""
    iw, ih = asset["size"]
    wf = min(wf, 0.99, 0.99 * ih * 16 / 9 / iw)
    wf = max(wf, STILL_MAX_UPSCALE ** -1 * W / iw + 1e-3)           # screen px per source px <= 4
    bw = wf * iw; bh = bw * 9 / 16
    cx = min(max(cx, bw / 2 / iw + 1e-4), 1 - bw / 2 / iw - 1e-4)
    cy = min(max(cy, bh / 2 / ih + 1e-4), 1 - bh / 2 / ih - 1e-4)
    return {"center": [round(cx, 5), round(cy, 5)], "width": round(wf, 5)}


VIEW_RECIPES = {"still_push_in": ((0.0, 0.0, 0.92), (0.0, 0.0, 0.62)), "still_pull_out": ((0.0, 0.0, 0.58), (0.0, 0.0, 0.9)),
                "still_pan": ((-0.12, 0.0, 0.62), (0.12, 0.0, 0.62))}


def still_view(asset, recipe):
    fx, fy = (asset.get("focus") or [0.5, 0.5])
    (dx0, dy0, w0), (dx1, dy1, w1) = VIEW_RECIPES[recipe]
    return {"from": fit_view(asset, fx + dx0, fy + dy0, w0), "to": fit_view(asset, fx + dx1, fy + dy1, w1), "ease": "in_out"}


# ------------------------------------------------------------------------------------------------ choice
def candidates(scene, kinds, assets, claims, allow_graphics):
    c = []
    for a in assets:
        if not a["exists"]: continue
        rel = relevance(scene, a)
        gap = year_gap(scene, a)
        hinted = scene["hints"].get("asset") == a["id"]
        if a.get("kind", "still") == "still":
            for recipe in ("still_push_in", "still_pull_out", "still_pan"):
                fit = {"still_push_in": 2.0 if "establish_place" in kinds or "number" in kinds else 1.2,
                       "still_pull_out": 1.8 if "change_over_time" in kinds or "locate" in kinds else 1.0,
                       "still_pan": 1.5 if "change_over_time" in kinds else 0.8}[recipe]
                c.append({"template": recipe, "asset": a["id"], "family": a.get("family") or a["id"], "fit": fit, "rel": rel, "year_gap": gap, "hinted": hinted})
        elif a.get("kind") == "video":
            c.append({"template": "video_sequence", "asset": a["id"], "family": a.get("family") or a["id"],
                      "fit": 2.6 if "change_over_time" in kinds else 1.0, "rel": rel, "year_gap": gap, "hinted": hinted})
    if allow_graphics:
        m = CALLOUT_RE.search(scene["text"])
        claim = match_claim(scene, claims)
        if m and claim:
            c.append({"template": "graphic_full", "gtype": "callout", "asset": None, "family": "graphic_number", "fit": 2.4, "rel": 0.0, "claim": claim["id"]})
        if scene["hints"].get("steps"):
            c.append({"template": "graphic_build_steps", "gtype": "flow", "asset": None, "family": "graphic_flow", "fit": 3.0, "rel": 0.0})
    return c


MONTH_RE = re.compile(r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+)?(1[89]\d\d|20\d\d)\b")


def callout_label(scene, claim, by_id, subject):
    """A short, whole-word label for a number graphic: the hint, else '<PLACE> · <DATE>' from the manifest and the sentence, else the
    claim cut at a word boundary (never mid-number)."""
    if scene["hints"].get("label"): return scene["hints"]["label"][:48]
    place = next((by_id[a].get("place") for a in sorted(subject) if a in by_id and by_id[a].get("place")), None)
    m = MONTH_RE.search(scene["text"])
    if place and m: return f"{place} \u00b7 {m.group(0)}".upper()[:48]
    if place: return place.upper()[:48]
    text = claim["text"]
    if len(text) <= 48: return text
    cut = text[:48].rsplit(" ", 1)[0].rstrip(",;:-")
    return cut + "\u2026"


def match_claim(scene, claims):
    ids = [x.strip() for x in scene["hints"].get("claims", "").split(",") if x.strip()]
    best = None
    for cl in claims:
        if not (cl.get("status") == "VERIFIED" and str(cl.get("source_url", "")).startswith("https://")): continue
        if ids and cl["id"] in ids: return cl
        a, b = set(re.findall(r"[a-z0-9]{4,}", cl["text"].lower())), set(re.findall(r"[a-z0-9]{4,}", scene["text"].lower()))
        ov = len(a & b) / max(1, len(a))
        if ov >= 0.5 and (best is None or ov > best[0]): best = (ov, cl)
    return best[1] if best else None


def score(c, history, t0, continuation=False):
    s = c["fit"] + 1.4 * min(c["rel"], 3.0)
    notes = []
    if c.get("hinted"): s += 6.0; notes.append("author hint (+6)")
    if c.get("year_gap") is not None:
        pen = 9.0 * min(c["year_gap"], 10) / 10          # a picture that shows another year must lose to one that shows the named year, even a repeated one
        if pen: s -= pen; notes.append(f"picture is {c['year_gap']} yr from the year narrated (-{pen:.1f})")
    last = history[-1] if history else None
    if last and last["template"] == c["template"] and c.get("asset") == last.get("asset"): s -= 4; notes.append("same template+asset as previous (-4)")
    elif last and last["template"] == c["template"]: s -= 1.2; notes.append("same template as previous (-1.2)")
    if last and last["family"] == c["family"]: s -= 2.5; notes.append("same visual family as previous (-2.5)")
    for h in history[-4:]:
        if not continuation and c.get("asset") and h.get("asset") == c["asset"] and t0 - h["t0"] < 45: s -= 3; notes.append("asset used <45 s ago (-3)"); break
    g_run = 0
    for h in reversed(history):
        if h["template"].startswith("graphic"): g_run += 1
        else: break
    if c["template"].startswith("graphic") and g_run >= 2: s -= 5; notes.append("third graphic in a row (-5, retention risk)")
    if c["template"].startswith("graphic") and g_run == 1: s -= 3.5; notes.append("graphic right after a graphic (-3.5)")
    if not c["template"].startswith("graphic") and g_run >= 1: s += 0.8; notes.append("returns to imagery (+0.8)")
    return s, notes


# ------------------------------------------------------------------------------------------------ build
def trigger_time(words, scene, key):
    """Start time of the first scene word that contains `key` (case-insensitive); else a third into the scene."""
    k = norm(key.split()[0]) if key else ""
    for i in range(scene["w0"], scene["w1"]):
        if k and k in norm(words[i]["text"]): return words[i]["start"]
    return words[scene["w0"]]["start"] + (words[scene["w1"] - 1]["end"] - words[scene["w0"]]["start"]) / 3


def label_for(scene, asset, kinds):
    h = scene["hints"]
    if h.get("label"): return h["label"][:LABEL_MAX].upper(), "tag", h["label"].split()[0] if h["label"] else ""
    if asset and asset.get("place") and re.search(r"\b" + re.escape(asset["place"].lower()) + r"\b", scene["text"].lower()):
        return asset["place"][:LABEL_MAX].upper(), "tag", asset["place"]
    m = CALLOUT_RE.search(scene["text"])
    if m: return f"{m.group(1)} {m.group(2)}".upper()[:LABEL_MAX], "stat", m.group(1)
    return None, None, None


def asset_needs(shots, tl_assets, scenes, words, duration):
    """Runs where one picture stays on screen over HOLD_S: the generator cannot fix them without inventing visuals, so it lists what to acquire."""
    ends = {sc["id"]: sc.get("end", duration) for sc in scenes}
    runs, cur = [], None
    for sh in shots:
        main = next((L["asset"] for L in sh["layers"] if L["type"] in ("still", "video")), None)
        if main and cur and cur["asset"] == main: cur["to"] = ends.get(sh["id"], duration)
        else:
            if cur: runs.append(cur)
            cur = {"asset": main, "from": sh["start"], "to": ends.get(sh["id"], duration)} if main else None
    if cur: runs.append(cur)
    return [{"asset": r["asset"], "from": round(r["from"], 2), "to": round(r["to"], 2), "seconds": round(r["to"] - r["from"], 1),
             "need": f"{r['to'] - r['from']:.0f} s on one picture: add a second picture of the same subject (other date or angle), a verified-number graphic or a video sequence"}
            for r in runs if r["to"] - r["from"] > HOLD_S]


def build(prod, allow_graphics=True, timings=None):
    raw = open(os.path.join(prod, "script.md"), encoding="utf-8").read()
    blocks = parse_script(raw)
    if not blocks: raise ValueError("script.md has no spoken text")
    vj = _json(os.path.join(prod, "voice", "narration.voice.json"))
    timing = timings or ("provider" if vj and vj.get("words") else "estimated")
    if timing == "provider":
        if not (vj and vj.get("words")): raise ValueError("--timings provider needs voice/narration.voice.json")
        words = [{"text": w["text"], "start": float(w["start"]), "end": float(w["end"])} for w in vj["words"]]
    else:
        words = estimate_words(blocks)
    al = align(blocks, words)
    assets = load_manifest(prod)
    scenes = build_scenes(blocks, words, {a["id"] for a in assets if a.get("kind") == "video"})
    claims = (_json(os.path.join(prod, "story", "claims.json"), {}) or {}).get("claims", [])
    duration = q(words[-1]["end"] + 1.5)
    plan = {"timing": timing, "alignment": al, "scenes": [], "gaps": [], "warnings": []}
    tl_assets, shots, history, specs = {}, [], [], []
    subject = set()

    def add_asset(a):
        if a["id"] in tl_assets: return
        if a.get("kind", "still") == "video":
            tl_assets[a["id"]] = {"src": a["src"], "kind": "video", "credit": a["credit"]}
        else:
            for k in ("credit", "source_url", "license", "retrieved"):
                if not a.get(k): raise ValueError(f"asset {a['id']} lacks {k} (provenance is mandatory)")
            tl_assets[a["id"]] = {"src": a["src"], "kind": "external_still", "credit": a["credit"], "label": a.get("place") or a["id"],
                                  "source_url": a["source_url"], "license": a["license"], "retrieved": a["retrieved"],
                                  **({"image_date": a["image_date"]} if a.get("image_date") else {})}
    by_id = {a["id"]: a for a in assets}
    cands_by_scene = {}
    for sc in scenes:
        kinds = classify(sc)
        cands = candidates(sc, kinds, assets, claims, allow_graphics)
        cands_by_scene[sc["id"]] = cands
        for c in cands:                                      # same subject as the last scene that named one: eligible, flagged as continuation
            if c["rel"] == 0 and c.get("asset") in subject: c["rel"] = 0.5; c["continuation"] = True
        relevant = [c for c in cands if c["rel"] > 0 or c["template"].startswith("graphic")]
        continuation = False
        if relevant:
            cands = relevant                               # never show a picture that has nothing to do with the sentence
            subject = {c["asset"] for c in relevant if c.get("asset") and c["rel"] > 0} or subject
        else:
            cands = [c for c in cands if c.get("asset") in subject]          # same subject as the last scene that named one
            continuation = bool(cands)
            for c in cands: c["rel"] = 0.5; c["continuation"] = True
        if not cands:
            plan["gaps"].append({"scene": sc["id"], "why": "no picture in assets/manifest.json relates to this scene; the previous shot simply continues", "text": sc["text"][:100]})
            continue
        scored = []
        for c in cands:
            s, notes = score(c, history, sc["start"], continuation)
            scored.append((s, c["template"] + ":" + str(c.get("asset")), c, notes))
        scored.sort(key=lambda x: (-x[0], x[1]))
        best_s, _, best, notes = scored[0]
        if continuation or best.get("continuation"): notes = notes + ["continuation: same subject as the previous shot, new view"]
        shot = {"id": sc["id"], "beat": " ".join(sc["text"].split()[:6]), "start": sc["start"], "info": first_sentence(sc["text"])[:60], "layers": []}
        dec = {"scene": sc["id"], "start": sc["start"], "end": sc["end"] if "end" in sc else duration, "kinds": kinds, "text": sc["text"],
               "chosen": {k: best.get(k) for k in ("template", "asset", "family", "gtype")}, "score": round(best_s, 2), "notes": notes,
               "alternatives": [{"template": c["template"], "asset": c.get("asset"), "score": round(s, 2)} for s, _, c, _ in scored[1:4]]}
        t0 = sc["start"]
        if best["template"].startswith("still"):
            a = by_id[best["asset"]]; add_asset(a)
            shot["layers"].append({"type": "still", "asset": a["id"], "view": still_view(a, best["template"])})
            lab, style, key = label_for(sc, a, kinds)
            if lab:
                lt0 = max(0.3, q(trigger_time(words, sc, key)) - t0)
                shot["layers"].append({"type": "label", "text": lab, "style": style, "slot": "upper", "info": lab, "t": [round(lt0, 3), round(lt0 + 2.6, 3)]})
                shot["layers"][0]["scrim"] = 0.4
        elif best["template"] == "video_sequence":
            a = by_id[best["asset"]]; add_asset(a)
            shot["layers"].append({"type": "video", "asset": a["id"], "credit": False, "captions": True})
        elif best["template"] == "graphic_full":
            cl = match_claim(sc, claims); m = CALLOUT_RE.search(sc["text"])
            gid = f"{sc['id']}-callout"
            val = float(m.group(1).replace(",", ""))
            specs.append({"type": "callout", "id": gid, "value": val, "unit": m.group(2), "label": callout_label(sc, cl, by_id, subject),
                          "context": sc["sents"][0][:90], "source": cl.get("source_name") or cl["source_url"], "decimals": 0 if val == int(val) else 1})
            shot["layers"].append({"type": "graphic", "asset": gid}); dec["graphic_claim"] = cl["id"]
        elif best["template"] == "graphic_build_steps":
            steps = [s_.strip() for s_ in sc["hints"]["steps"].split("|") if s_.strip()][:6]
            gid = f"{sc['id']}-flow"
            specs.append({"type": "flow", "id": gid, "title": (sc["hints"].get("label") or "Process")[:50], "steps": steps, "build": True,
                          "source": sc["hints"].get("source", "Original schematic · steps from the narration")})
            shot["layers"].append({"type": "graphic", "asset": gid, "_steps": len(steps), "_sent_starts": sc["sent_starts"]})
        history.append({"template": best["template"], "asset": best.get("asset"), "family": best["family"], "t0": sc["start"], "scene": sc["id"]})
        shot["visual_family"] = best["family"]
        shots.append(shot); plan["scenes"].append(dec)
    if not shots: raise ValueError("nothing could be planned: assets/manifest.json has no usable asset")
    plan["needs"] = asset_needs(shots, tl_assets, scenes, words, duration)
    for d_ in plan["scenes"]:
        gap_ = next((c.get("year_gap") for c in [x for x in cands_by_scene.get(d_["scene"], []) if x.get("asset") == d_["chosen"].get("asset")][:1]), None)
        if gap_:
            plan["needs"].append({"scene": d_["scene"], "asset": d_["chosen"].get("asset"), "need": f"a picture dated within the narrated year (the best available is {gap_} yr away): acquire one with /yt-satellite or choose a script wording that does not name the year"})
    tl = {"version": 3, "profile": "long", "grid": "grid.json", "assets": tl_assets, "shots": shots, "end": {"seconds": duration},
          "render": {"segment_s": 60},
          "meta": {"generator": "tools/autopilot/storyboard.py", "timing": timing,
                   "timing_note": "provider word times" if timing == "provider" else "ESTIMATED timing (2.38 words/s): a proof only, not frame-accurate; rebuild after the paid narration exists"}}
    return tl, plan, specs, words


# ------------------------------------------------------------------------------------------------ graphics, validation, repair
def render_graphics(prod, tl, specs):
    """Render the yt-graphics specs, then replace the placeholder graphic layers with the real PNG assets (and build steps)."""
    if not specs: return []
    gdir = os.path.join(prod, "graphics")
    os.makedirs(gdir, exist_ok=True)
    for old in os.listdir(gdir):                               # generated folder: drop outputs of an earlier plan so stale PNGs never linger
        if old.endswith((".png", ".json")): os.remove(os.path.join(gdir, old))
    spec_path = os.path.join(gdir, "spec.json")
    with open(spec_path, "w", encoding="utf-8") as f: json.dump({"schema": "yt-graphics/1", "graphics": specs}, f, indent=1)
    r = subprocess.run([sys.executable, os.path.join(SKILLS, "yt-graphics", "graphics.py"), spec_path, "--out-dir", gdir], capture_output=True, text=True)
    if r.returncode != 0:
        raise ValueError("yt-graphics failed: " + (r.stdout + r.stderr)[-400:])
    problems = []
    for shot in tl["shots"]:
        new = []
        for L in shot["layers"]:
            if L["type"] != "graphic": new.append(L); continue
            gid = L["asset"]
            meta = _json(os.path.join(gdir, gid + ".json"), {})
            steps = meta.get("steps") or []                       # build-step PNGs in order; the last one is the finished graphic
            use = steps if (L.get("_steps") and steps) else [gid + ".png"]
            for n, fn in enumerate(use, 1):
                aid = f"{gid}_{n}"
                tl["assets"][aid] = {"src": f"graphics/{fn}", "kind": "graphic", "credit": "Original graphic · sources on the image", "group": gid}
                layer = {"type": "graphic", "asset": aid}
                if n > 1:
                    starts = L.get("_sent_starts") or []
                    frac = (n - 1) / len(use)
                    layer["t"] = [round(max(0.5, frac * 6.0), 3), None]      # replaced below by word-anchored times
                new.append(layer)
        shot["layers"] = new
    return problems


def anchor_steps(tl, scenes_by_id, words):
    """Build steps of a graphic appear on the sentence/phrase they illustrate (word-anchored), not on a fixed clock."""
    for shot in tl["shots"]:
        sc = scenes_by_id.get(shot["id"])
        g = [L for L in shot["layers"] if L["type"] == "graphic"]
        if not sc or len(g) < 2: continue
        n = len(g)
        k = max(1, len(sc["sent_starts"]))
        for i, L in enumerate(g[1:], 1):
            idx = sc["sent_starts"][min(k - 1, round(i * k / n))] if k > 1 else sc["w0"] + round(i * (sc["w1"] - sc["w0"]) / n)
            L["t"] = [round(max(0.5, q(words[min(idx, len(words) - 1)]["start"]) - shot["start"]), 3), None]


def run_plan(prod, timeline="timeline.json"):
    r = subprocess.run([sys.executable, os.path.join(SKILLS, "yt-render", "render.py"), "--timeline", timeline], cwd=prod, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"status": "error", "error": (r.stdout + r.stderr)[-500:]}


def repair(tl, err):
    """Known technical errors -> a fix. Returns a description, or None when the error is not one we can repair safely."""
    m = re.search(r"shot (\w[\w-]*): the (from|to) view of '(\w[\w-]*)' (leaves the image|would magnify)", err)
    if m:
        sid, end, aid = m.groups()[:3]
        for s in tl["shots"]:
            if s["id"] == sid:
                for L in s["layers"]:
                    if L["type"] == "still" and L["asset"] == aid:
                        for e in ("from", "to"): L["view"][e]["width"] = min(0.99, max(L["view"][e]["width"] * 1.25, 0.5)); L["view"][e]["center"] = [0.5, 0.5]
                        return f"widened the view of {aid} in {sid}"
    m = re.search(r"(shots\[(\d+)\]\.layers\[(\d+)\])\.text must be 1-40", err)
    if m:
        s = tl["shots"][int(m.group(2))]["layers"][int(m.group(3))]; s["text"] = s["text"][:LABEL_MAX]
        return f"shortened a label in {m.group(1)}"
    m = re.search(r"shot (\S+) starts at or before shot (\S+)", err)
    if m:
        ids = [s["id"] for s in tl["shots"]]; i = ids.index(m.group(1))
        tl["shots"][i]["start"] = round(tl["shots"][i - 1]["start"] + 1 / FPS, 4)
        return f"moved {m.group(1)} one frame after {m.group(2)}"
    m = re.search(r"shot (\S+) starts after the end", err)
    if m:
        tl["shots"] = [s for s in tl["shots"] if s["id"] != m.group(1)]
        return f"dropped {m.group(1)} (after the end)"
    return None


def validate_and_repair(prod, tl, rounds=3):
    log = []
    for n in range(rounds + 1):
        with open(os.path.join(prod, "timeline.json"), "w", encoding="utf-8") as f: json.dump(tl, f, indent=1, ensure_ascii=False)
        res = run_plan(prod)
        if res.get("status") != "error" and "plan" in res:
            return res, log
        err = res.get("error", "")
        fix = repair(tl, err)
        log.append({"round": n + 1, "error": err[:300], "fix": fix})
        if not fix: return res, log
    return res, log


def hold_report(res):
    comp = (res.get("plan") or {}).get("compositions") or {}
    return {k: (len(v) if k == "resets" and isinstance(v, list) else v) for k, v in comp.items()}


def write_outputs(prod, tl, plan, res, log):
    os.makedirs(os.path.join(prod, "story"), exist_ok=True)
    plan["renderer_plan"] = {"status": res.get("status"), "warnings": (res.get("plan") or {}).get("warnings", []),
                             "compositions": (res.get("plan") or {}).get("compositions"), "expected_duration": (res.get("plan") or {}).get("expected_duration")}
    plan["repairs"] = log
    with open(os.path.join(prod, "story", "storyboard.plan.json"), "w", encoding="utf-8") as f: json.dump(plan, f, indent=1, ensure_ascii=False)
    L = ["# Storyboard (generated - edit timeline.json, or the script/hints, then rerun `storyboard.py plan`)", "",
         f"Timing: **{plan['timing']}**" + ("  ·  ESTIMATED, a proof only" if plan["timing"] == "estimated" else ""), ""]
    for d in plan["scenes"]:
        c = d["chosen"]
        L.append(f"- **{d['scene']}** {d['start']:.1f}s · {c['template']} · asset `{c.get('asset')}` · family `{c['family']}` · score {d['score']} · {', '.join(d['kinds'])}")
        L.append(f"  - “{d['text'][:140]}”")
        for n in d["notes"]: L.append(f"  - {n}")
    if plan["gaps"]:
        L += ["", "## Gaps (not faked)"] + [f"- {g['scene']}: {g['why']}" for g in plan["gaps"]]
    if plan["renderer_plan"]["warnings"]:
        L += ["", "## Renderer warnings"] + [f"- {w}" for w in plan["renderer_plan"]["warnings"]]
    with open(os.path.join(prod, "story", "storyboard.md"), "w", encoding="utf-8") as f: f.write("\n".join(L) + "\n")


def plan_cmd(prod, allow_graphics=True, timings=None):
    tl, plan, specs, words = build(prod, allow_graphics, timings)
    with open(os.path.join(prod, "grid.json"), "w", encoding="utf-8") as f: json.dump(DUMMY_GRID, f)
    render_graphics(prod, tl, specs)
    # word-anchored build steps
    raw = open(os.path.join(prod, "script.md"), encoding="utf-8").read()
    blocks = parse_script(raw); align(blocks, words)
    scenes_by_id = {s["id"]: s for s in build_scenes(blocks, words, {a["id"] for a in load_manifest(prod) if a.get("kind") == "video"})}
    anchor_steps(tl, scenes_by_id, words)
    for shot in tl["shots"]:
        for L in shot["layers"]:
            L.pop("_steps", None); L.pop("_sent_starts", None)
    res, log = validate_and_repair(prod, tl)
    write_outputs(prod, tl, plan, res, log)
    ok = res.get("status") != "error" and "plan" in res
    return {"ok": ok, "scenes": len(plan["scenes"]), "gaps": plan["gaps"], "repairs": log, "timing": plan["timing"],
            "renderer_warnings": plan["renderer_plan"]["warnings"], "compositions": hold_report(res), "error": None if ok else res.get("error")}


# ------------------------------------------------------------------------------------------------ preview
def preview_cmd(prod, start=0.0, end=15.0, confirm=False):
    tl = _json(os.path.join(prod, "timeline.json"))
    if not tl: raise ValueError("no timeline.json; run plan first")
    sub = {k: v for k, v in tl.items() if k not in ("voice", "captions")}
    shots = []
    for i, s in enumerate(tl["shots"]):
        s_end = tl["shots"][i + 1]["start"] if i + 1 < len(tl["shots"]) else tl["end"]["seconds"]
        if s_end <= start or s["start"] >= end: continue
        n = json.loads(json.dumps(s)); n["start"] = round(max(s["start"], start) - start, 4)
        shift = max(0.0, start - s["start"])
        if shift:
            for L in n["layers"]:
                if "t" in L: L["t"] = [max(0.0, round(L["t"][0] - shift, 4)), None if L["t"][1] is None else max(0.0, round(L["t"][1] - shift, 4))]
        shots.append(n)
    shots[0]["start"] = 0
    used = {L["asset"] for s in shots for L in s["layers"] if "asset" in L}
    sub["assets"] = {k: v for k, v in tl["assets"].items() if k in used}
    sub["shots"] = shots
    dur = min(end, tl["end"]["seconds"]) - start
    sub["end"] = {"seconds": round(dur, 3)}
    sub["meta"] = dict(tl.get("meta", {}), preview=[start, end], note="silent proof; " + tl.get("meta", {}).get("timing_note", ""))
    pdir_ = os.path.join(prod, "preview"); os.makedirs(pdir_, exist_ok=True)
    tpath = os.path.join(prod, "preview", "timeline_preview.json")
    # the renderer resolves sources relative to the timeline folder, so write the preview timeline next to the production root
    tpath = os.path.join(prod, "timeline_preview.json")
    with open(tpath, "w", encoding="utf-8") as f: json.dump(sub, f, indent=1, ensure_ascii=False)
    cmd = [sys.executable, os.path.join(SKILLS, "yt-render", "render.py"), "--timeline", "timeline_preview.json"]
    if confirm: cmd += ["--output", "preview/proof.mp4", "--confirm", "--overwrite"]
    r = subprocess.run(cmd, cwd=prod, capture_output=True, text=True)
    try: out = json.loads(r.stdout)
    except ValueError: out = {"status": "error", "error": (r.stdout + r.stderr)[-500:]}
    return out


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 2 or a[0] not in ("plan", "preview"):
        print(__doc__); return 0
    os.environ.setdefault("ORBITAL_PRODUCTIONS", os.path.join(ROOT, "productions"))
    prod = os.path.join(os.environ["ORBITAL_PRODUCTIONS"], a[1])
    def opt(n, d=None): return a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else d
    try:
        if a[0] == "plan": r = plan_cmd(prod, "--no-graphics" not in a, opt("--timings"))
        else: r = preview_cmd(prod, float(opt("--start", 0)), float(opt("--end", 15)), "--confirm" in a)
    except (ValueError, OSError, KeyError) as x:
        print(json.dumps({"ok": False, "error": f"{type(x).__name__}: {x}"})); return 2
    print(json.dumps(r, indent=1, ensure_ascii=False, default=str))
    return 0 if r.get("ok", r.get("status") != "error") else 1


if __name__ == "__main__":
    sys.exit(main())
