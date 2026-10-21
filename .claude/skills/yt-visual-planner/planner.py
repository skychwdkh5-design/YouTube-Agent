#!/usr/bin/env python3
"""yt-visual-planner: claims + script + satellite stacks -> episode.json and graphics_spec.json (no hand-written JSON).

Deterministic rules (no prose, no invention):
 - every visual is justified by claim ids found in that chapter's script lines ({C#} tags);
 - original claim with scale_km  -> wide scale graphic (arrow vs the real frame width)
 - >= 2 media/org claims          -> "what was reported" flow graphic (labels = claim.short)
 - observation with years [a, b]  -> wipe a->b + same-ground compare graphic;  with callouts -> annotated hero frame
 - tiers (PROMISED / REPORTED / OBSERVED) graphic for the limits chapter
 - date labels ("OCT 2022") come from the stack's provenance, never typed.
Claims declare what is drawable (short, years, focus, callouts, scale_km) in research/notes.json; the planner adds nothing else.
Output asserts every graphic's claims so yt-facts and yt-visualcheck can audit them.
"""
import argparse, json, os, re, sys

MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
TAG = re.compile(r"\{(C\d+(?:\s*,\s*C\d+)*)\}")
CH_RE = re.compile(r"^##\s+([a-z0-9_]+)\s*[:\-]")
CREDIT = "Contains modified Copernicus Sentinel data {y}"
SMALL_CREDIT = "Sentinel-2 · ESA"


class PlanError(Exception):
    pass


def chapter_text_lines(script):
    out, cur = {}, None
    for line in script.splitlines():
        m = CH_RE.match(line.strip())
        if m:
            cur = m.group(1); out[cur] = []; continue
        if cur and line.strip() and not line.strip().startswith(("#", "[")):
            out[cur].append(line.strip())
    return out


def chapter_claims(script):
    out, order, cur = {}, [], None
    for line in script.splitlines():
        s = line.strip()
        m = CH_RE.match(s)
        if m:
            cur = m.group(1); order.append(cur); out[cur] = []; continue
        if cur and s and not s.startswith(("#", "[")):
            for g in TAG.findall(s):
                out[cur] += [x.strip() for x in g.split(",") if x.strip() not in out[cur]]
    return out, order


def stack_info(root, name):
    p = os.path.join(root, "evidence", name)
    g, pv = os.path.join(p, "grid.json"), os.path.join(p, "provenance.json")
    if not (os.path.exists(g) and os.path.exists(pv)):
        return None
    grid = json.load(open(g))
    prov = {s["id"]: s for s in json.load(open(pv))["scenes"]}
    return {"grid": grid, "prov": prov, "w_km": grid["width"] * grid["pixel_m"] / 1000, "h_km": grid["height"] * grid["pixel_m"] / 1000}


def clamp_center(info, center, width_km):
    """Keep a square-ish view of width_km inside the stack (planner views must never leave the imagery)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yt-geo"))
    import numpy as np, geostack as g
    G = info["grid"]
    cx, cy = g.lonlat_to_utm(np.array([center[0]]), np.array([center[1]]), G["epsg"])
    hw = width_km * 500 * 1.02
    hh = hw * 9 / 16
    x0, y1 = G["x0"], G["y_top"]
    x1, y0 = x0 + G["width"] * G["pixel_m"], y1 - G["height"] * G["pixel_m"]
    cx = min(max(cx[0], x0 + hw), x1 - hw)
    cy = min(max(cy[0], y0 + hh), y1 - hh)
    lo, la = g.utm_to_lonlat(np.array([cx]), np.array([cy]), G["epsg"])
    return [round(float(lo[0]), 5), round(float(la[0]), 5)]


def date_label(prov, year):
    s = prov.get(f"y{year}")
    if not s:
        raise PlanError(f"no scene for {year} in provenance")
    d = s["datetime"]
    return f"{MON[int(d[5:7]) - 1]} {d[:4]}"


def plan(root):
    notes = json.load(open(os.path.join(root, "research", "notes.json")))
    geo = notes.get("geo") or {}
    if not geo.get("stacks"):
        raise PlanError("research/notes.json needs geo.stacks (aoi, years) - the AOI is a research decision")
    claims = {c["id"]: c for c in json.load(open(os.path.join(root, "claims.json")))["claims"]}
    script = open(os.path.join(root, "script.md"), encoding="utf-8").read()
    used, order = chapter_claims(script)
    chap_text = chapter_text_lines(script)
    main = geo["stacks"][0]["name"]
    wide = next((s["name"] for s in geo["stacks"] if s.get("role") == "wide"), None)
    mi = stack_info(root, main)
    if not mi:
        raise PlanError(f"stack {main} not built yet (evidence stage)")
    years = sorted(int(y) for y in geo["stacks"][0]["years"])
    focus, seg = geo.get("focus"), geo.get("segment") or geo.get("focus")
    grid_rel = f"evidence/{main}/grid.json"
    assets = {f"y{y}": {"src": f"evidence/{main}/y{y}.png", "label": str(y), "credit": CREDIT.format(y=y)} for y in years}
    gfx, g_assets = [], {}

    def add_graphic(g, ids, credit_year=None):
        gfx.append(g)
        g_assets[g["id"]] = {"src": f"graphics/{g['id']}.png", "kind": "graphic", "credit": CREDIT.format(y=credit_year or years[-1]), "group": g["id"], "claims": ids}

    orig = [c for c in claims.values() if c["tier"] == "original" and c.get("scale_km") and c["confidence"] != "low"]
    if orig and wide:
        wi = stack_info(root, wide)
        if wi:
            c = orig[0]
            w = int(min(wi["w_km"], wi["h_km"] * 16 / 9) * 0.9 // 5 * 5) or 10
            wy = max(int(y) for y in next(s for s in geo["stacks"] if s["name"] == wide)["years"])
            f2 = geo.get("wide_focus") or focus
            add_graphic({"type": "geo", "id": "g_scale", "title": f"Announced length: {c['scale_km']} km. This frame: about {w} km.", "source": f"Copernicus Sentinel-2 L2A, resampled to {int(wi['grid']['pixel_m'])} m",
                         "credit": CREDIT.format(y=wy), "show_credit": False, "date": date_label(wi["prov"], wy), "image": {"stack": f"evidence/{wide}/y{wy}.png", "grid": f"evidence/{wide}/grid.json", "center": f2, "width_km": w},
                         "arrows": [{"from": [f2[0] - w * 0.0045, f2[1] + w * 0.0007], "to": [f2[0] + w * 0.0045, f2[1] + w * 0.0007], "label": f"{c['scale_km']} km announced length"}],
                         "graticule": False, "scale_bar": True}, [c["id"]], wy)
    rep = sorted([c for c in claims.values() if c["tier"] in ("media", "org") and c["confidence"] != "low"], key=lambda c: c.get("date", ""))
    if len(rep) >= 2:
        steps = ([orig[0]["short"]] if orig else []) + [c["short"] for c in rep][:5]
        add_graphic({"type": "flow", "id": "g_reports", "title": "What was reported", "source": "; ".join(sorted({c.get('attribution', '') for c in rep}))[:110], "steps": steps[:6],
                     "arrow_labels": ["then"] * (len(steps[:6]) - 1), "build": False}, ([orig[0]["id"]] if orig else []) + [c["id"] for c in rep][:5])
    obs = [c for c in claims.values() if c["tier"] == "observation" and c["confidence"] != "low"]
    if orig and rep and obs:
        add_graphic({"type": "flow", "id": "g_tiers", "title": "Keep three things apart", "source": "claims " + ", ".join([orig[0]["id"], rep[0]["id"], obs[0]["id"]]),
                     "steps": [f"PROMISED: {orig[0]['short']}", f"REPORTED: {rep[-1]['short']}", f"OBSERVED: {obs[0]['short']}"], "arrow_labels": ["vs", "vs"], "build": False}, [orig[0]["id"], rep[-1]["id"], obs[0]["id"]])
    for c in obs:
        ys = c.get("years") or []
        if len(ys) == 2:
            f = clamp_center(mi, c.get("focus") or focus, c.get("compare_km", 8))
            add_graphic({"type": "compare", "id": f"g_cmp_{ys[0]}_{ys[1]}_{c['id'].lower()}", "title": c["short"], "source": "Copernicus Sentinel-2 L2A, same orbit and season",
                         "left": {"geo": {"stack": f"evidence/{main}/y{ys[0]}.png", "grid": grid_rel, "center": f, "width_km": c.get("compare_km", 8)}, "label": date_label(mi["prov"], ys[0]), "credit": SMALL_CREDIT},
                         "right": {"geo": {"stack": f"evidence/{main}/y{ys[1]}.png", "grid": grid_rel, "center": f, "width_km": c.get("compare_km", 8)}, "label": date_label(mi["prov"], ys[1]), "credit": SMALL_CREDIT}},
                        [c["id"]], ys[1])
        if c.get("callouts"):
            add_graphic({"type": "geo", "id": f"g_hero_{c['id'].lower()}", "title": c["short"], "source": "Copernicus Sentinel-2 L2A, 10 m", "credit": CREDIT.format(y=years[-1]), "show_credit": False, "date": date_label(mi["prov"], years[-1]),
                         "image": {"stack": f"evidence/{main}/y{years[-1]}.png", "grid": grid_rel, "center": c.get("focus") or seg, "width_km": c.get("hero_km", 6)},
                         "callouts": c["callouts"], "scale_bar": True}, [c["id"]], years[-1])
    assets.update(g_assets)
    gid = {k: v for k, v in g_assets.items()}

    def G(prefix, ids=None):
        return [k for k in gid if k.startswith(prefix)]

    def img(y, zoom, focus_=None, label=True, claims_=None, **k):
        if claims_:
            claims_ = [i for i in claims_ if claims.get(i, {}).get("visual", True)] or None
        d = {"asset": f"y{y}", "zoom": zoom}
        if focus_:
            d["focus"] = focus_
        if label:
            d["label"] = {"text": date_label(mi["prov"], y), "style": "year", "exempt": True, "date_year": y}
        if claims_:
            d["claims"] = claims_
        d.update(k)
        return d

    def gr(name, ids, m=5):
        d = {"asset": name, "kind": "graphic", "min_s": m, "claims": ids, "anchor": "claim"}
        if name == "g_reports" and orig:
            d["anchor_claims"] = [i for i in ids if i != orig[0]["id"]]       # the graphic opens with the promise, but it belongs where the REPORTS are spoken
        return d

    import itertools
    cyc = itertools.cycle(years)
    chapters, hook_done, dropped = [], False, []
    first, last = years[0], years[-1]
    mid = years[len(years) // 2]
    for cid in order:
        cl = [claims[i] for i in used.get(cid, []) if i in claims]
        vis, seen = [], set()
        words = len(TAG.sub("", " ".join(l for l in chap_text.get(cid, [])).replace("**", "")).split())
        if cid == "hook" or not chapters:
            if "g_scale" in gid:
                vis.append(gr("g_scale", gid["g_scale"]["claims"], 3.5))
            o = next((c for c in cl if c["tier"] == "observation" and len(c.get("years") or []) == 2), None) or next((c for c in obs if len(c.get("years") or []) == 2), None)
            if o and o["years"][0] != first:         # "year after year": two establishing beats (two different years, each with its date label) before the narrator's year-bound words
                vis.append(img(first, [22, 14], None))
                if len(years) > 1:
                    vis.append(img(years[1], [8, 16], None))
            vis.append(img(o["years"][0] if o else first, [15, 8], None, anchor="year" if o else None))
            if o:
                a, b = o["years"]
                vis.append({"wipe": [f"y{a}", f"y{b}"], "zoom": [8, 6.5], "family": f"wipe_{a}_{b}", "min_s": 4, "claims": [o["id"]], "anchor": "year"})
            k = next((c for c in cl + obs if c.get("callouts")), None)
            d = img(last, [6.5, 2.8], seg, False, [k["id"]] if k else None)
            if k:
                d["label"] = {"text": k["short"], "style": "tag", "claim": k["id"]}
            vis.append(d)
            chapters.append({"id": cid, "visuals": vis})
            continue
        for c in cl:
            t = c["tier"]
            if t == "original" and "g_scale" in gid and "g_scale" not in seen:
                vis.append(gr("g_scale", gid["g_scale"]["claims"], 5)); seen.add("g_scale")
                vis.append(img(last, [15, 9]))
            elif t in ("media", "org") and "g_reports" in gid and "g_reports" not in seen:
                vis.append(gr("g_reports", gid["g_reports"]["claims"], 6)); seen.add("g_reports")
                vis.append(img(next(cyc), [14, 8]))
                vis.append(img(next(cyc), [8, 14], seg))
            elif t == "science" and "sci" not in seen:
                vis.append(img(first, [15, 9])); vis.append(img(mid, [9, 15], seg)); vis.append(img(last, [15, 7])); vis.append(img(next(cyc), [7, 15], seg)); seen.add("sci")
            elif t == "observation":
                ys = c.get("years") or []
                if len(ys) == 2 and f"obs{c['id']}" not in seen:
                    seen.add(f"obs{c['id']}")
                    ck = c.get("compare_km")
                    z = [ck * 1.6, ck * 1.1] if ck else [15, 10]
                    vis.append(img(ys[0], z, c.get("focus"), claims_=[c["id"]], anchor="year"))
                    gn = next((k for k in gid if k.startswith(f"g_cmp_{ys[0]}_{ys[1]}_{c['id'].lower()}")), None)
                    if gn:
                        vis.append(gr(gn, [c["id"]], 6))
                    vis.append({"wipe": [f"y{ys[0]}", f"y{ys[1]}"], "zoom": [ck * 1.2, ck * 0.9] if ck else [10, 7], "focus": c.get("focus"), "family": f"wipe_{ys[0]}_{ys[1]}", "min_s": 4, "claims": [c["id"]], "anchor": "year"})
                elif len(ys) > 2 and f"obs{c['id']}" not in seen:
                    seen.add(f"obs{c['id']}")
                    for n_, y in enumerate(ys):             # alternate in/out by >= 1.6x so every year is a real composition change
                        vis.append(img(y, [15, 9] if n_ % 2 == 0 else [9, 15], c.get("focus"), claims_=[c["id"]], anchor="year"))
                elif f"obs{c['id']}" not in seen:
                    seen.add(f"obs{c['id']}")
                    vis.append(img(next(cyc) if not c.get("visual", True) else last, [10, 6], c.get("focus") or seg, claims_=[c["id"]]))
                hn = next((k for k in gid if k.startswith(f"g_hero_{c['id'].lower()}")), None)
                if hn:
                    vis.append(gr(hn, [c["id"]], 6))
            elif t == "hypothesis" and "g_tiers" in gid and "g_tiers" not in seen:
                vis.append(gr("g_tiers", gid["g_tiers"]["claims"], 5)); seen.add("g_tiers")
        if cid == "close":                       # closing recap in the order the narrator says it: time-lapse, PROMISED, REPORTED, OBSERVED, then pull back (distinct families: no long holds)
            o2 = next((c for c in obs if len(c.get("years") or []) == 2), None)
            vis = []
            if o2:
                vis.append({"wipe": [f"y{first}", f"y{last}"], "zoom": [16, 10], "family": "wipe_recap", "min_s": 3, "claims": [o2["id"]]})
            for name in ("g_scale", "g_reports"):
                if name in gid:
                    vis.append(gr(name, gid[name]["claims"], 4))
            hn = next((k for k in gid if o2 and k.startswith(f"g_hero_{o2['id'].lower()}")), None)
            if hn:
                vis.append(gr(hn, [o2["id"]], 5))
            vis.append(img(last, [10, 6], seg, family="close_view", min_s=3))
            vis.append(img(last, [8, 24], None, family="close_wide", min_s=3))       # last line: pull back to the whole stretch
        if not vis:
            vis.append(img(last, [15, 9]))
        if len(vis) > 10:
            dropped.append({"chapter": cid, "dropped": [v.get("asset") or str(v.get("wipe")) for v in vis[10:]]})
        vis = vis[:10]                           # no chapter is a slideshow of everything it cites; what was dropped is reported
        need = -(-int(words / 2.45 - 5 * len([v for v in vis if v.get("kind") == "graphic"])) // 8)     # one picture per ~8 s of narration that graphics do not cover
        k_ = 0
        while len([v for v in vis if v.get("kind") != "graphic"]) < min(need, 8):
            vis.append(img(next(cyc), [15, 8] if k_ % 2 == 0 else [8, 15], seg if k_ % 2 else None)); k_ += 1
        while len([v for v in vis if v.get("kind") != "graphic"]) < 1:
            vis.append(img(last, [15, 9]))
        dur = words / 2.45
        if len(vis) < 3 and dur >= 9:
            vis.append(img(mid, [9, 14]))
        dur = words / 2.45
        while len(vis) > 1 and 2.0 * len([v for v in vis if v.get("kind") == "graphic"]) + 2.5 * len([v for v in vis if v.get("kind") != "graphic"]) > dur:
            gone = vis.pop()                    # the chapter is too short for this many pictures: drop from the end and say so
            dropped.append({"chapter": cid, "dropped": [gone.get("asset") or str(gone.get("wipe"))], "reason": f"chapter is {dur:.1f}s"})
        chapters.append({"id": cid, "visuals": vis})
    ep = {"slug": os.path.basename(os.path.abspath(root)), "title": notes.get("title", "TBD"), "titles": notes.get("titles", []), "grid": grid_rel, "focus": focus,
          "graphics": "graphics_spec.json", "evidence": {"stacks": [{k: v for k, v in s.items() if k != "role"} for s in geo["stacks"]]}, "assets": assets, "chapters": chapters,
          "generated_by": "yt-visual-planner", "planner_dropped": dropped}
    spec = {"schema": "yt-graphics/1", "graphics": gfx}
    return ep, spec


def write(root):
    ep, spec = plan(root)
    for name, obj in (("episode.json", ep), ("graphics_spec.json", spec)):
        tmp = os.path.join(root, name + ".part")
        json.dump(obj, open(tmp, "w"), indent=1, ensure_ascii=False)
        os.replace(tmp, os.path.join(root, name))
    return {"status": "ok", "chapters": len(ep["chapters"]), "visuals": sum(len(c["visuals"]) for c in ep["chapters"]), "graphics": [g["id"] for g in spec["graphics"]], "dropped": ep["planner_dropped"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".")
    a = ap.parse_args(argv)
    try:
        r = write(a.root)
        print(json.dumps(r, indent=1))
        return 0
    except (PlanError, OSError, KeyError, ValueError) as e:
        print(json.dumps({"status": "error", "error": f"{type(e).__name__}: {e}"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
