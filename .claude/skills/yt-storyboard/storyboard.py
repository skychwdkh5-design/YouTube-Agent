#!/usr/bin/env python3
"""yt-storyboard: script + verified claims + available imagery -> timed storyboard and a yt-render v3 (long) timeline.

episode.json supplies the visual vocabulary (assets, chapters -> visuals); script.md supplies the spoken text and
therefore the timing (words / pace, or real word timings from yt-voice when present). The plan is checked by the
existing yt-render planner (no render, no cost) and its pacing warnings go into report.md.

Outputs: <episode>/timeline.json (render media root = the episode folder) and <episode>/story/{storyboard.json, labels.json, report.md}
"""
import argparse, hashlib, json, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(SK, "yt-geo"))
GRAPHIC_PUSH = 0.04        # slow push-in on every full-frame graphic: none is ever a still
PACE_WPS = 2.45            # spoken words per second (~147 wpm) when no voice timings exist
MAX_SHOT_S, MIN_SHOT_S = 7.0, 2.5     # yt-render long warns above 8 s static
TAG = re.compile(r"\{(?:C\d+(?:\s*,\s*C\d+)*|L)\}")


class StoryError(Exception):
    pass


def parse_script(text):
    """{chapter_id: [words]} from '## id: Title' headings; directions, tags and headings are not spoken."""
    ch, order, cur = {}, [], None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"##\s+([a-z0-9_]+)\s*[:\-]", s)
        if m:
            cur = m.group(1)
            order.append(cur)
            ch[cur] = []
            continue
        if not s or s.startswith(("#", "[", ">", "---", "<!--")) or cur is None:
            continue
        s = TAG.sub("", re.sub(r"\*\*", "", s))
        ch[cur] += s.split()
    return ch, order


def parse_sentences(text):
    """{chapter_id: [{"w0": first word index inside the chapter, "n": words, "text": str, "claims": [ids]}]}: one entry per tagged or untagged sentence.
    Word counts follow parse_script exactly, so indexes line up with the voice word timings."""
    out, cur = {}, None
    for line in text.splitlines():
        st = line.strip()
        m = re.match(r"##\s+([a-z0-9_]+)\s*[:\-]", st)
        if m:
            cur = m.group(1); out[cur] = []; continue
        if not st or st.startswith(("#", "[", ">", "---", "<!--")) or cur is None:
            continue
        st = st.replace("**", "")
        done = sum(x["n"] for x in out[cur])
        pos = 0
        for mt in list(TAG.finditer(st)) + [None]:
            seg = st[pos:mt.start()] if mt else st[pos:]
            if mt:
                pos = mt.end()
            words = TAG.sub("", seg).split()
            if not words:
                continue
            ids = re.findall(r"C\d+", mt.group(0)) if mt else []
            out[cur].append({"w0": done, "n": len(words), "text": " ".join(words), "claims": ids})
            done += len(words)
    return out


def _fixed(v):
    """Full-frame visuals that keep their own on-screen time: yt-graphics images and external stills (photos, NASA images)."""
    return v.get("kind") in ("graphic", "still")


def _visual_year(v):
    """The year a visual is meant to be on screen for: set explicitly by the planner (anchor: year) for a year image or the reveal of a wipe."""
    if v.get("anchor") != "year" or _fixed(v):
        return None
    m = re.fullmatch(r"y(\d{4})", str(v["wipe"][1] if "wipe" in v else v.get("asset", "")))
    return m.group(1) if m else None


def _claim_sentence(v, sents, after):
    """Index of the first sentence after word index `after` that cites any claim of graphic v, else None."""
    ids = set(v.get("anchor_claims") or v.get("claims") or [])
    return next((k for k, x in enumerate(sents) if x["w0"] > after and ids & set(x["claims"])), None)


def place_by_claims(vis, durs, sents, word_time, t0):
    """Reorder so each claim-anchored graphic (anchor: claim) sits among the map visuals at the time its claim is spoken, not at the chapter start.
    A graphic whose claim is made in the first 2.5 s stays where it is."""
    starts = [t0 + sum(durs[:i]) for i in range(len(vis))]
    base, inserts = [], []
    for i, v in enumerate(vis):
        if v.get("anchor") == "claim" and _fixed(v):
            k = _claim_sentence(v, sents, -1)
            tt = word_time(sents[k]["w0"]) - 0.3 if k is not None else None
            if tt is not None and tt > t0 + 2.5:
                inserts.append((tt, i, v)); continue
        base.append((starts[i], v))
    if not inserts:
        return vis
    out = [v for _, v in sorted(base, key=lambda x: x[0])]
    pos_t = [t for t, _ in sorted(base, key=lambda x: x[0])]
    for tt, _, v in sorted(inserts, key=lambda x: x[0]):
        pos = next((n for n, t_ in enumerate(pos_t) if t_ >= tt and n > 0), len(out))
        out.insert(pos, v); pos_t.insert(pos, tt)
    return out


def anchor_durations(vis, durs, sents, word_time, t0, t1, min_of):
    """Move shot boundaries so a year-anchored visual appears when the narrator says its year (the word itself, not the sentence).
    word_time(i) -> start seconds of chapter word i. Visuals between two anchors share the time proportionally.
    Returns (new durations, report). An anchor that cannot be honoured (year not said later, or no room) is reported and skipped."""
    n = len(vis)
    starts = [t0 + sum(durs[:i]) for i in range(n)]
    toks = [(x["w0"] + k, w) for x in sents for k, w in enumerate(x["text"].split())]
    fixed, rep, cursor = {0: t0}, [], -1
    for i, v in enumerate(vis):
        y = _visual_year(v)
        if i == 0 or (y is None and not (v.get("anchor") == "claim" and _fixed(v))):
            continue
        if y is None:                                    # a graphic citing claims: when the first sentence that cites them begins
            k = _claim_sentence(v, sents, cursor)
            hit = sents[k]["w0"] if k is not None else None
            y = "claim"
        else:
            hit = next((wi for wi, w in toks if wi > cursor and re.search(rf"(?<!\d){y}(?!\d)", w)), None)
        if hit is None:
            rep.append({"visual": i, "year": y, "status": "the narrator does not say this year after the previous anchor"}); continue
        want = word_time(hit) - (min(0.5, durs[i] / 4) if "wipe" in v else 0.3 if y == "claim" else 0.15)
        prev_i = max(fixed)
        floor_ = fixed[prev_i] + sum(min_of(vis[k]) for k in range(prev_i, i))
        ceil_ = t1 - sum(min_of(vis[k]) for k in range(i, n))
        got = min(max(want, floor_), ceil_)
        if abs(got - want) > 1.0:
            rep.append({"visual": i, "year": y, "status": f"cannot reach {want:.1f}s (room {floor_:.1f}-{ceil_:.1f}s)"}); continue
        fixed[i] = got
        cursor = hit
        rep.append({"visual": i, "year": y, "target": round(want, 2), "was": round(starts[i], 2), "now": round(got, 2)})
    pts = sorted(fixed) + [n]
    new = [0.0] * n
    for a, b in zip(pts, pts[1:]):
        t_a = fixed[a]
        t_b = fixed[b] if b in fixed else t1
        seg = range(a, b)
        gs = [k for k in seg if _fixed(vis[k])]
        ms = [k for k in seg if k not in gs]
        spare = (t_b - t_a) - sum(durs[k] for k in gs)
        if ms and spare >= sum(min_of(vis[k]) for k in ms):      # graphics keep their own time; the map beats absorb the stretch
            for k in gs:
                new[k] = durs[k]
            tot = sum(durs[k] for k in ms)
            for k in ms:
                new[k] = spare * durs[k] / tot
        else:
            tot = sum(durs[a:b]) or 1.0
            for k in seg:
                new[k] = (t_b - t_a) * durs[k] / tot
    for k in range(1, n):                              # a graphic is never stretched past 7 s: it starts a little after its claim and the map before it holds longer
        if _fixed(vis[k]) and new[k] > 7.0 and not _fixed(vis[k - 1]):
            new[k - 1] += new[k] - 7.0
            new[k] = 7.0
    return new, rep


def chapter_times(chapters, order, voice_meta=None):
    """Start/end seconds per chapter: from real word timings if given, else words / PACE_WPS."""
    out, t = {}, 0.0
    if voice_meta:
        words = voice_meta["words"]
        i = 0
        for cid in order:
            n = len(chapters[cid])
            if i + n > len(words):
                raise StoryError(f"voice timings have {len(words)} words, script needs {i + n}")
            out[cid] = (words[i]["start"], words[i + n - 1]["end"] if n else words[i]["start"])
            i += n
        # chapters are contiguous: a chapter starts where the previous one ended
        prev = 0.0
        for cid in order:
            s, e = out[cid]
            out[cid] = (prev, e)
            prev = e
        return out, "voice"
    for cid in order:
        d = max(len(chapters[cid]) / PACE_WPS, 0.0)
        out[cid] = (t, t + d)
        t += d
    return out, "estimate"


def _bounds(grid):
    import geostack as g
    x0, y1 = grid["x0"], grid["y_top"]
    x1, y0 = x0 + grid["width"] * grid["pixel_m"], y1 - grid["height"] * grid["pixel_m"]
    return g, (x0, y0, x1, y1)


def fit_view(grid, center, width_km):
    """Clamp a 16:9 view so it stays inside the stack; returns (center_lonlat, width_km)."""
    import numpy as np
    g, (x0, y0, x1, y1) = _bounds(grid)
    w = min(width_km, (x1 - x0) / 1000 * 0.98, (y1 - y0) / 1000 * 16 / 9 * 0.98)
    hw, hh = w * 500 * 1.02, w * 500 * 9 / 16 * 1.02          # 2 % margin: the renderer refuses a view that touches the edge
    cx, cy = g.lonlat_to_utm(np.array([center[0]]), np.array([center[1]]), grid["epsg"])
    cx = min(max(cx[0], x0 + hw), x1 - hw)
    cy = min(max(cy[0], y0 + hh), y1 - hh)
    lo, la = g.utm_to_lonlat(np.array([cx]), np.array([cy]), grid["epsg"])
    return [round(float(lo[0]), 5), round(float(la[0]), 5)], round(w, 3)


def split_duration(total, lo=MIN_SHOT_S, hi=MAX_SHOT_S):
    n = max(1, math.ceil(total / hi))
    while n > 1 and total / n < lo:
        n -= 1
    return [total / n] * n


def build(ep, root, voice_meta=None):
    sc, order = parse_script(open(os.path.join(root, ep.get("script", "script.md")), encoding="utf-8").read())
    grid = json.load(open(os.path.join(root, ep["grid"])))
    times, timing = chapter_times(sc, order, voice_meta)
    want = [c["id"] for c in ep["chapters"]]
    if want != order:
        raise StoryError(f"chapters in episode.json {want} do not match script headings {order}")
    shots, labels, fam_prev, anchors = [], [], None, {}
    sentences = parse_sentences(open(os.path.join(root, ep.get("script", "script.md")), encoding="utf-8").read())
    chap_base, acc = {}, 0
    for c_ in order:
        chap_base[c_] = acc
        acc += len(sc[c_])
    for chap in ep["chapters"]:
        cid = chap["id"]
        t0, t1 = times[cid]
        vis = chap["visuals"]
        if not vis:
            raise StoryError(f"chapter {cid} has no visuals")
        total = t1 - t0
        if total < 0.5:
            raise StoryError(f"chapter {cid} has no spoken text")
        def alloc(vis):
            """Graphics keep a fixed on-screen time (min_s, at most 7 s); the remaining time is shared by map visuals. Returns (durations, set of graphic indexes)."""
            gdur = {i: min(max(v.get("min_s", 4.0), 2.0), 7.0) for i, v in enumerate(vis) if _fixed(v)}
            maps = [i for i in range(len(vis)) if i not in gdur]
            rest = total - sum(gdur.values())
            if maps and rest < MIN_SHOT_S * len(maps):
                # not enough time: shrink graphics proportionally (never below 2 s) before giving up
                need = MIN_SHOT_S * len(maps) - rest
                room = sum(d - 2.0 for d in gdur.values())
                if room < need:
                    raise StoryError(f"chapter {cid}: {total:.1f}s is too short for {len(vis)} visuals")
                f = 1 - need / room
                gdur = {i: 2.0 + (d - 2.0) * f for i, d in gdur.items()}
                rest = total - sum(gdur.values())
            if not maps:
                gdur = {i: d * total / sum(gdur.values()) for i, d in gdur.items()}
                if max(gdur.values()) > 9.0:
                    raise StoryError(f"chapter {cid}: graphics would sit {max(gdur.values()):.1f}s on screen; add visuals")
            mw = {i: max(vis[i].get("min_s", MIN_SHOT_S), 0.1) for i in maps}
            return [gdur[i] if i in gdur else rest * mw[i] / sum(mw.values()) for i in range(len(vis))], set(gdur)
        durs, gset = alloc(vis)
        sents = sentences.get(cid) or []
        if sents:
            base_w = chap_base[cid]
            nw = max(1, sum(x["n"] for x in sents))
            tof = (lambda wi: voice_meta["words"][base_w + wi]["start"]) if voice_meta else (lambda wi: t0 + total * wi / nw)
            vis = place_by_claims(vis, durs, sents, tof, t0)           # a graphic that cites claims sits where the narrator makes them
            durs, gset = alloc(vis)
            durs, arep = anchor_durations(vis, durs, sents, tof, t0, t1, lambda v: 2.0 if _fixed(v) else MIN_SHOT_S)
            if arep:
                anchors[cid] = arep
        t = t0
        for i, v in enumerate(vis):
            dur = durs[i]
            parts = [dur] if i in gset else split_duration(dur)
            for k, d in enumerate(parts):
                shots.append(_shot(ep, grid, chap, v, k, len(parts), t, d, labels, len(shots)))
                t += d
    for i, s in enumerate(shots):
        s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else round(times[order[-1]][1], 3)
    total = shots[-1]["end"]
    return {"schema": "yt-storyboard/1", "timing": timing, "duration": round(total, 3), "chapters": {c: [round(a, 2), round(b, 2)] for c, (a, b) in times.items()},
            "anchors": anchors, "shots": shots}, labels


def _shot(ep, grid, chap, v, k, n, t, d, labels, idx):
    sid = f"{chap['id']}_{idx:03d}"        # unique across the whole storyboard
    s = {"id": sid, "chapter": chap["id"], "start": round(t, 3), "dur": round(d, 3), "family": v.get("family") or f"{v.get('asset') or 'wipe'}_{chap['id']}"}
    if v.get("claims"):
        s["claims"] = list(v["claims"])
    if v.get("kind") == "graphic":
        s["layers"] = [{"type": "graphic", "asset": v["asset"], "t": [0, None], "push": GRAPHIC_PUSH}]
        s["info"] = v.get("info", v["asset"])
        a = ep["assets"][v["asset"]]
        labels.append({"text": f"graphic:{v['asset']}", "claims": a.get("claims") or [], "exempt": bool(a.get("exempt")), "shot": sid})
        return s
    if v.get("kind") == "still":
        a = ep["assets"][v["asset"]]
        wide, tight = (1.0, 0.84) if v.get("zoom_in", True) else (0.84, 1.0)
        s["layers"] = [{"type": "still", "asset": v["asset"], "view": {"from": {"center": [0.5, 0.5], "width": wide}, "to": {"center": [0.5, 0.5], "width": tight}}, "credit": True, "scrim": 0.0}]
        s["info"] = v.get("info", v["asset"])
        s["media"] = a.get("media_id")
        if v.get("label"):
            s["layers"].append({"type": "label", "text": v["label"]["text"], "style": v["label"].get("style", "tag"), "slot": v["label"].get("slot", "upper"), "t": [0.6, None]})
            labels.append({"text": v["label"]["text"], "claim": None, "exempt": True, "shot": sid})
        return s
    if "wipe" in v and k > 0:             # a long wipe slot is ONE reveal followed by the revealed picture, never the same wipe played again
        end_w = (v.get("zoom") or [12, 6])[1]
        v = dict({kk: vv for kk, vv in v.items() if kk != "wipe"}, asset=v["wipe"][1], zoom=[end_w * 0.4, end_w * 0.3])   # cut in on the revealed picture (a real composition change), then keep pushing
        kz = 0
    else:
        kz = k
    focus = v.get("focus") or chap.get("focus") or ep.get("focus")
    z0, z1 = (v.get("zoom") or [12, 6])
    if kz % 2 == 1:                     # beats of one visual alternate wide and tight (>= 1.5x between beats): each is a real composition change, never a long hold
        z0, z1 = max(z1 * 0.6, 2.5), max(z0 * 0.6, 2.5)
    c0, w0 = fit_view(grid, focus, z0)
    c1, w1 = fit_view(grid, v.get("focus_to") or focus, z1)
    s["camera"] = {"from": {"center": c0, "width_km": w0}, "to": {"center": c1, "width_km": w1}}
    layers = []
    if "wipe" in v:
        a, b = v["wipe"]
        layers += [{"type": "image", "asset": a}, {"type": "wipe", "from": a, "to": b, "t": [min(0.5, d / 4), min(0.5, d / 4) + min(1.7, d / 2)]}]
        s["info"] = f"wipe {a}->{b}"
    else:
        layers.append({"type": "image", "asset": v["asset"]})
        s["info"] = v.get("info", v["asset"])
    if v.get("label") and k == 0:
        lab = v["label"]
        layers.append({"type": "label", "text": lab["text"], "style": lab.get("style", "tag"), "slot": lab.get("slot", "upper"), "t": [min(0.8, d / 3), None]})
        labels.append({"text": lab["text"], "claim": lab.get("claim"), "exempt": lab.get("exempt", False), "shot": sid})
    s["layers"] = layers
    return s


def diversity(sb, ep=None, max_map_run=4):
    """Visual-variety audit of a storyboard (VISUAL_STYLE_V3): kinds, scale classes, longest run of satellite-map shots, adjacent same-scale shots.
    kind: map (camera over the imagery stack) / graphic (yt-graphics) / still (photo or NASA image) / video. scale: wide >= 10 km, mid 4-10 km, tight < 4 km (at the end of the move)."""
    kinds, runs, run, run_start, worst = [], [], 0, 0.0, (0, 0.0, 0.0)
    prev_scale, same_scale = None, []
    for s in sb["shots"]:
        l0 = s["layers"][0]["type"] if s.get("layers") else "image"
        kind = "graphic" if l0 == "graphic" else "still" if l0 == "still" else "video" if l0 == "video" else "map"
        kinds.append(kind)
        if kind == "map":
            w = (s.get("camera") or {}).get("to", {}).get("width_km", 8)
            sc = "wide" if w >= 10 else "mid" if w >= 4 else "tight"
            if run == 0:
                run_start = s["start"]
            run += 1
            end = s["start"] + s["dur"]
            if run > worst[0]:
                worst = (run, run_start, end)
            if prev_scale == sc:
                same_scale.append(s["id"])
            prev_scale = sc
        else:
            run, prev_scale = 0, None
    n = len(kinds)
    share = {k: round(kinds.count(k) / n, 3) for k in ("map", "graphic", "still", "video")}
    warns = []
    if worst[0] > max_map_run:
        warns.append(f"{worst[0]} satellite-map shots in a row ({worst[1]:.0f}-{worst[2]:.0f} s, {worst[2] - worst[1]:.0f} s): more than {max_map_run}; add a photo, video, graphic or map of a different kind")
    if len(same_scale) > max(2, n // 6):
        warns.append(f"{len(same_scale)} neighbouring map shots end at the same scale class; alternate wide / mid / tight")
    if share["still"] + share["video"] == 0:
        warns.append("no photo or video at all: the film is satellite maps and graphics only")
    pending = []
    for p in (ep or {}).get("media_pending") or []:
        p = dict(p)
        if p.get("status") != "REJECTED":                   # where it WOULD go once its rights are VERIFIED: the middle map shot of its chapter (the planner inserts it for real then)
            ch = (sb.get("chapters") or {}).get(p.get("scene"))
            cand = [s for s in sb["shots"] if ch and ch[0] - 0.01 <= s["start"] < ch[1] and (s["layers"][0]["type"] if s.get("layers") else "image") == "image" or (ch and ch[0] - 0.01 <= s["start"] < ch[1] and s.get("camera"))]
            if cand:
                m = cand[len(cand) // 2]
                p["would_replace"] = {"shot": m["id"], "start": m["start"], "dur": round(min(m["dur"], 6.0), 1)}
        pending.append(p)
    return {"rule": "visual-diversity/1", "max_map_run": max_map_run, "longest_map_run": {"shots": worst[0], "from": round(worst[1], 1), "to": round(worst[2], 1)}, "kind_share": share,
            "same_scale_neighbours": len(same_scale), "warnings": warns, "status": "WARN" if warns else "OK", "media_pending": pending}


def to_timeline(ep, sb, root, voice=None, captions=None):
    assets = {k: {kk: vv for kk, vv in a.items() if kk not in ("claims", "exempt", "media_id", "pending")} for k, a in ep["assets"].items()}   # renderer rejects unknown keys
    tl = {"version": 3, "profile": "long", "grid": ep["grid"], "assets": assets, "shots": []}
    for s in sb["shots"]:
        o = {"id": s["id"], "start": s["start"], "visual_family": re.sub(r"[^a-z0-9_]", "_", str(s["family"]).lower()), "info": s["info"], "layers": s["layers"]}
        if "camera" in s:
            o["camera"] = s["camera"]
        tl["shots"].append(o)
    if voice:
        tl["voice"] = voice
        tl["captions"] = {"src": captions, "preset": "default", "style": "kinetic"} if captions else None
        if not captions:
            tl.pop("captions")
        tl["end"] = {"after_last_word": 1.5}
    else:
        tl["end"] = {"seconds": max(1, round(sb["duration"] + 1.0, 2))}
    return tl


def validate_with_renderer(tl_path, root):
    """yt-render plan only (no --confirm): structural errors and pacing warnings."""
    r = subprocess.run([sys.executable, os.path.join(SK, "yt-render", "render.py"), "--timeline", tl_path], cwd=root, capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return {"status": "error", "error": (r.stderr or r.stdout)[:300]}
    return {"status": d.get("status"), "error": d.get("error"), "warnings": d.get("warnings") or (d.get("plan") or {}).get("warnings") or []}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--episode", required=True, help="folder with episode.json and script.md")
    ap.add_argument("--voice-meta", help="yt-voice .voice.json (real word timings); default: estimate from words")
    ap.add_argument("--captions")
    a = ap.parse_args(argv)
    root = a.episode
    try:
        ep = json.load(open(os.path.join(root, "episode.json"), encoding="utf-8"))
        vm = json.load(open(a.voice_meta)) if a.voice_meta else None
        sb, labels = build(ep, root, vm)
        voice = {"src": os.path.relpath(os.path.join(os.path.dirname(os.path.abspath(a.voice_meta)), vm["audio"]), root), "meta": os.path.relpath(a.voice_meta, root)} if vm else None
        tl = to_timeline(ep, sb, root, voice, a.captions)
        out = os.path.join(root, "story")
        os.makedirs(out, exist_ok=True)
        div = diversity(sb, ep)
        for name, obj, dst in (("storyboard.json", sb, out), ("timeline.json", tl, root), ("labels.json", labels, out), ("diversity.json", div, out)):
            tmp = os.path.join(dst, name + ".part")
            json.dump(obj, open(tmp, "w"), indent=1)
            os.replace(tmp, os.path.join(dst, name))
        chk = validate_with_renderer("timeline.json", root)
        sha = hashlib.sha256(json.dumps(sb, sort_keys=True).encode()).hexdigest()[:16]
        rep = [f"# Storyboard report", "", f"- timing: {sb['timing']}; duration {sb['duration']} s; shots {len(sb['shots'])}; plan hash {sha}",
               f"- renderer plan: {chk['status']} {chk.get('error') or ''}", "- chapters: " + ", ".join(f"{c} {v[0]}-{v[1]}s" for c, v in sb["chapters"].items())]
        rep += [f"- warning: {w}" for w in chk.get("warnings", [])]
        rep += [f"- diversity {div['status']}: map {div['kind_share']['map']:.0%} / graphic {div['kind_share']['graphic']:.0%} / photo {div['kind_share']['still']:.0%} / video {div['kind_share']['video']:.0%}; longest satellite-map run {div['longest_map_run']['shots']} shots"]
        rep += [f"- diversity warning: {w}" for w in div["warnings"]]
        rep += [f"- media PENDING (not in the render, rights not VERIFIED): {p['id']} [{p['status']}] for scene {p['scene']} {p.get('page_url', '')}" for p in div["media_pending"]]
        if sb["duration"] < 360 or sb["duration"] > 720:
            rep.append(f"- warning: duration {sb['duration']:.0f}s is outside the 6-12 minute target; add real content, never filler")
        rep += ["", "Shots:"] + [f"- {s['start']:>7.2f}s +{s['dur']:.1f}s {s['chapter']}: {s['info']}" for s in sb["shots"]]
        open(os.path.join(out, "report.md"), "w").write("\n".join(rep) + "\n")
        res = {"status": "ok" if chk["status"] in ("confirm_required", "ok") else "blocked", "shots": len(sb["shots"]), "duration": sb["duration"],
               "timing": sb["timing"], "renderer": chk, "hash": sha, "out": out}
        print(json.dumps(res, indent=1))
        return 0 if res["status"] == "ok" else 1
    except (StoryError, OSError, KeyError, ValueError) as e:
        print(json.dumps({"status": "error", "error": f"{type(e).__name__}: {e}"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
