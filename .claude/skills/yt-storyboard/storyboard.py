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
    shots, labels, fam_prev = [], [], None
    for chap in ep["chapters"]:
        cid = chap["id"]
        t0, t1 = times[cid]
        vis = chap["visuals"]
        if not vis:
            raise StoryError(f"chapter {cid} has no visuals")
        total = t1 - t0
        if total < 0.5:
            raise StoryError(f"chapter {cid} has no spoken text")
        # graphics keep a fixed on-screen time (min_s, at most 7 s); the remaining time is shared by map visuals
        gdur = {i: min(max(v.get("min_s", 4.0), 2.0), 7.0) for i, v in enumerate(vis) if v.get("kind") == "graphic"}
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
        t = t0
        for i, v in enumerate(vis):
            dur = gdur[i] if i in gdur else rest * mw[i] / sum(mw.values())
            parts = [dur] if i in gdur else split_duration(dur)
            for k, d in enumerate(parts):
                shots.append(_shot(ep, grid, chap, v, k, len(parts), t, d, labels, len(shots)))
                t += d
    for i, s in enumerate(shots):
        s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else round(times[order[-1]][1], 3)
    total = shots[-1]["end"]
    return {"schema": "yt-storyboard/1", "timing": timing, "duration": round(total, 3), "chapters": {c: [round(a, 2), round(b, 2)] for c, (a, b) in times.items()},
            "shots": shots}, labels


def _shot(ep, grid, chap, v, k, n, t, d, labels, idx):
    sid = f"{chap['id']}_{idx:03d}"        # unique across the whole storyboard
    s = {"id": sid, "chapter": chap["id"], "start": round(t, 3), "dur": round(d, 3), "family": v.get("family") or v.get("asset") or "wipe"}
    if v.get("claims"):
        s["claims"] = list(v["claims"])
    if v.get("kind") == "graphic":
        s["layers"] = [{"type": "graphic", "asset": v["asset"], "t": [0, None]}]
        s["info"] = v.get("info", v["asset"])
        a = ep["assets"][v["asset"]]
        labels.append({"text": f"graphic:{v['asset']}", "claims": a.get("claims") or [], "exempt": bool(a.get("exempt")), "shot": sid})
        return s
    focus = v.get("focus") or chap.get("focus") or ep.get("focus")
    z0, z1 = (v.get("zoom") or [12, 6])
    if k % 2 == 1:                      # alternate direction between beats of the same visual: a real composition change
        z0, z1 = z1, z0
    if n > 1:
        z0, z1 = z0 * (1 + 0.25 * k), z1 * (1 + 0.25 * k)
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


def to_timeline(ep, sb, root, voice=None, captions=None):
    assets = {k: {kk: vv for kk, vv in a.items() if kk not in ("claims", "exempt")} for k, a in ep["assets"].items()}   # renderer rejects unknown keys
    tl = {"version": 3, "profile": "long", "grid": ep["grid"], "assets": assets, "shots": []}
    for s in sb["shots"]:
        o = {"id": s["id"], "start": s["start"], "visual_family": re.sub(r"[^a-z0-9_]", "_", str(s["family"]).lower()), "info": s["info"], "layers": s["layers"]}
        if "camera" in s:
            o["camera"] = s["camera"]
        tl["shots"].append(o)
    if voice:
        tl["voice"] = voice
        tl["captions"] = {"src": captions, "preset": "default"} if captions else None
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
        for name, obj, dst in (("storyboard.json", sb, out), ("timeline.json", tl, root), ("labels.json", labels, out)):
            tmp = os.path.join(dst, name + ".part")
            json.dump(obj, open(tmp, "w"), indent=1)
            os.replace(tmp, os.path.join(dst, name))
        chk = validate_with_renderer("timeline.json", root)
        sha = hashlib.sha256(json.dumps(sb, sort_keys=True).encode()).hexdigest()[:16]
        rep = [f"# Storyboard report", "", f"- timing: {sb['timing']}; duration {sb['duration']} s; shots {len(sb['shots'])}; plan hash {sha}",
               f"- renderer plan: {chk['status']} {chk.get('error') or ''}", "- chapters: " + ", ".join(f"{c} {v[0]}-{v[1]}s" for c, v in sb["chapters"].items())]
        rep += [f"- warning: {w}" for w in chk.get("warnings", [])]
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
