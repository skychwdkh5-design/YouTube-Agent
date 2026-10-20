#!/usr/bin/env python3
"""yt-visualcheck: for every claim-bearing on-screen item - the source, the frame, the allowed wording, and what was actually verified.

Statuses (never upgraded by matching ids alone):
  VERIFIED_SOURCE       the text is an attributed statement; the claim registry holds its source (yt-facts checks the wording)
  VERIFIED_DATA         a machine check on real data passed (date label vs scene metadata; measured presence/absence/length)
  REVIEWED_BY_<who>     a reviewer looked at THIS exact frame (sha256) and recorded what they saw; not machine-verified
  NEEDS_VISUAL_REVIEW   the text asserts something about the picture and no machine check exists: a frame crop is written for review
  FAIL                  a check contradicts the text, the claim is missing/low confidence, or a review says "does_not_support"
Exit 0 only when no item is FAIL and none is NEEDS_VISUAL_REVIEW.
qa/visual_review.json: {"reviews":[{"item","frame_sha256","reviewer":"agent|owner","verdict":"supports|does_not_support|unclear","note"}]}
"""
import argparse, hashlib, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "yt-geo"))
MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
CONF = {"high": 3, "medium": 2, "low": 1}
SRC_TIERS = {"original", "media", "org", "science"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def crop_frame(root, stack_rel, grid, center, width_km, out):
    import numpy as np, geostack as g
    from PIL import Image
    im = Image.open(os.path.join(root, stack_rel)).convert("RGB")
    cx, cy = g.lonlat_to_utm(np.array([center[0]]), np.array([center[1]]), grid["epsg"])
    px = grid["pixel_m"]
    c, r = (cx[0] - grid["x0"]) / px, (grid["y_top"] - cy[0]) / px
    hw = width_km * 500 / px
    hh = hw * 9 / 16
    box = (max(0, int(c - hw)), max(0, int(r - hh)), min(im.size[0], int(c + hw)), min(im.size[1], int(r + hh)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.crop(box).resize((960, 540)).save(out)
    return sha(out)


def check_ndwi_years(root, chk, claim_years=None):
    """Measured presence/absence (and length) of the water-like dark feature per year from evidence/ndwi.json."""
    p = os.path.join(root, chk["file"])
    if not os.path.exists(p):
        return None, f"{chk['file']} missing"
    d = json.load(open(p))["years"]
    bad = []
    for y in chk.get("present", []):
        s = d.get(str(y))
        if not s or s.get("water_like_px") is None or s["water_like_px"] < chk.get("min_px", 100):
            bad.append(f"{y}: expected presence, got {s and s.get('water_like_px')}")
        elif "length_km" in chk and not (chk["length_km"][0] <= s.get("extent_km", 0) <= chk["length_km"][1]):
            bad.append(f"{y}: extent {s.get('extent_km')} km outside {chk['length_km']}")
    for y in chk.get("absent", []):
        s = d.get(str(y))
        if not s or s.get("water_like_px") is None or s["water_like_px"] > chk.get("max_px_absent", 20):
            bad.append(f"{y}: expected absence, got {s and s.get('water_like_px')}")
    return (not bad), "; ".join(bad) or f"present {chk.get('present')}, absent {chk.get('absent')} confirmed by NDWI counts"


def view_contains(grid, center, width_km, pt, margin=0.1):
    import numpy as np, geostack as g
    cx, cy = g.lonlat_to_utm(np.array([center[0], pt[0]]), np.array([center[1], pt[1]]), grid["epsg"])
    hw = width_km * 500 * (1 - margin)
    return abs(cx[1] - cx[0]) <= hw and abs(cy[1] - cy[0]) <= hw * 9 / 16


def check_scene_meta(prov, chk):
    sc = [prov.get(f"y{y}") for y in chk["years"]]
    if not all(sc):
        return False, "scene missing"
    plats = {s["platform"] for s in sc}
    dates = {s["datetime"][:10] for s in sc}
    ok = len(plats) >= chk.get("platforms_min", 1) and len(dates) >= chk.get("dates_min", 1)
    return ok, f"{len(dates)} dates, platforms {sorted(plats)} from provenance.json"


def check_ndwi_extent(root, chk):
    p = os.path.join(root, chk["file"])
    if not os.path.exists(p):
        return None, f"{chk['file']} missing"
    d = json.load(open(p))["years"]
    bad = [f"{y}: extent {d.get(y, {}).get('extent_km')} km outside {rng}" for y, rng in chk["years"].items() if not (rng[0] <= (d.get(y) or {}).get("extent_km", -1) <= rng[1])]
    return (not bad), "; ".join(bad) or "measured extents inside the claimed ranges: " + ", ".join(f"{y}: {d[y]['extent_km']} km" for y in chk["years"])


def run(root, stage_review=True):
    claims = {c["id"]: c for c in json.load(open(os.path.join(root, "claims.json")))["claims"]}
    ep = json.load(open(os.path.join(root, "episode.json")))
    sb = json.load(open(os.path.join(root, "story", "storyboard.json")))
    spec = {g["id"]: g for g in json.load(open(os.path.join(root, ep["graphics"])))["graphics"]} if ep.get("graphics") and os.path.exists(os.path.join(root, ep["graphics"])) else {}
    main = ep["evidence"]["stacks"][0]["name"]
    prov = {s["id"]: s for s in json.load(open(os.path.join(root, "evidence", main, "provenance.json")))["scenes"]}
    grid = json.load(open(os.path.join(root, ep["grid"])))
    reviews = []
    rp = os.path.join(root, "qa", "visual_review.json")
    if os.path.exists(rp):
        reviews = json.load(open(rp)).get("reviews", [])
    items = []

    def allowed(ids):
        w = sorted({claims[i].get("wording") for i in ids if i in claims and claims[i].get("wording")})
        return {"wording": w, "forbid": sorted({f for i in ids if i in claims for f in claims[i].get("forbid", [])})}

    def finish(it):
        ids = it["claims"]
        miss = [i for i in ids if i not in claims]
        low = [i for i in ids if i in claims and claims[i]["tier"] != "hypothesis" and CONF[claims[i]["confidence"]] < 2]
        if miss or low:
            it["status"], it["why"] = "FAIL", f"missing claims {miss}" if miss else f"claims below medium confidence {low}"
        it["source"] = [{"claim": i, "tier": claims[i]["tier"], "attribution": claims[i].get("attribution"), "url": claims[i].get("url"), "date": claims[i].get("date"),
                         "evidence": claims[i].get("evidence")} for i in ids if i in claims]
        it["allowed"] = allowed(ids)
        items.append(it)

    def image_assertion(it, frames):
        """Machine check if every claim defines one; otherwise a reviewable frame."""
        ids = it["claims"]
        results = []
        for i in ids:
            chk = claims[i].get("check") if i in claims else None
            anchors = [c_["at"] for c_ in claims[i].get("callouts", [])] if i in claims else []
            anchor = claims[i].get("anchor") if i in claims else None
            pts = ([anchor] if anchor else anchors[:1]) if i in claims else []
            if chk and pts and frames and not all(view_contains(grid, c_, w_, pts[0]) for (_, c_, w_) in frames):
                results.append((None, "data check exists, but this view does not contain the measured location"))
                continue
            if chk and not pts:
                results.append((None, "data check exists but the claim names no location to confirm the frame covers"))
                continue
            if chk and chk.get("kind") == "scene_meta":
                results.append(check_scene_meta(prov, chk))
            elif chk and chk.get("kind") == "ndwi_years":
                ok, why = check_ndwi_years(root, chk)
                results.append((ok, why))
            elif chk and chk.get("kind") == "ndwi_extent":
                results.append(check_ndwi_extent(root, chk))
            else:
                results.append((None, "no machine check for this assertion"))
        if results and all(r[0] is True for r in results):
            it["status"], it["why"] = "VERIFIED_DATA", "; ".join(r[1] for r in results) + " [data check + the view contains the location; what the image looks like is not machine-judged]"
            return
        if any(r[0] is False for r in results):
            it["status"], it["why"] = "FAIL", "; ".join(r[1] for r in results if r[0] is False)
            return
        fl = []
        for k, (stack_rel, center, wkm) in enumerate(frames):
            out = os.path.join(root, "qa", "frames", re.sub(r"[^A-Za-z0-9_.-]", "_", it["id"]) + f"_{k}.png")
            fl.append({"file": os.path.relpath(out, root), "sha256": crop_frame(root, stack_rel, grid, center, wkm, out), "stack": stack_rel, "center": center, "width_km": wkm})
        it["frames"] = fl
        sig = sorted(ids)
        found = []
        for f_ in fl:
            rv = next((r for r in reviews if r.get("frame_sha256") == f_["sha256"] and sorted(r.get("claims", [])) == sig), None)
            found.append(rv)
            f_["review"] = rv["verdict"] if rv else None
        if fl and any(r and r["verdict"] == "does_not_support" for r in found):
            bad = next(r for r in found if r and r["verdict"] == "does_not_support")
            it["status"], it["why"] = "FAIL", "review: does_not_support - " + bad.get("note", "")
        elif fl and all(r and r["verdict"] == "supports" for r in found):
            who = sorted({r["reviewer"].upper() for r in found})
            it["status"], it["why"] = "REVIEWED_BY_" + "_".join(who), " | ".join(r.get("note", "") for r in found)[:300]
        else:
            miss = sum(1 for r in found if not r or r["verdict"] != "supports")
            it["status"], it["why"] = "NEEDS_VISUAL_REVIEW", f"{miss} of {len(fl)} frames not reviewed (or review unclear/stale); a reviewer must look at each frame"

    for shot in sb["shots"]:
        # 1) text labels drawn on the shot
        for lab in [l for l in json.load(open(os.path.join(root, "story", "labels.json"))) if l.get("shot") == shot["id"] and not str(l["text"]).startswith("graphic:")]:
            it = {"id": f"{shot['id']}:label:{lab['text']}", "kind": "label", "text": lab["text"], "shot": shot["id"], "claims": [lab["claim"]] if lab.get("claim") else []}
            m = re.fullmatch(r"([A-Z]{3}) (\d{4})", lab["text"])
            if m:                                                   # date label: verify against scene metadata
                s = prov.get(f"y{m.group(2)}")
                ok = bool(s) and MON[int(s["datetime"][5:7]) - 1] == m.group(1) and s["datetime"][:4] == m.group(2)
                it.update(status="VERIFIED_DATA" if ok else "FAIL", why=f"scene {s and s['itemId']} acquired {s and s['datetime'][:10]}" if s else "no scene for that year", frame={"asset": f"y{m.group(2)}"})
                finish(it); continue
            if not it["claims"]:
                it.update(status="FAIL", why="text without a claim id"); finish(it); continue
            cam = shot.get("camera", {}).get("to")
            lay = next((l for l in shot["layers"] if l["type"] == "image"), None)
            if claims.get(it["claims"][0], {}).get("tier") in SRC_TIERS:
                it.update(status="VERIFIED_SOURCE", why="attributed statement; wording checked by yt-facts"); finish(it); continue
            if cam and lay:
                image_assertion(it, [(ep["assets"][lay["asset"]]["src"], cam["center"], cam["width_km"])])
            else:
                it.update(status="NEEDS_VISUAL_REVIEW", why="no frame available")
            finish(it)
        # 2) graphics
        g0 = shot["layers"][0] if shot.get("layers") else {}
        if g0.get("type") == "graphic":
            gid = g0["asset"]
            a = ep["assets"][gid]
            it = {"id": f"{shot['id']}:graphic:{gid}", "kind": "graphic", "text": gid, "shot": shot["id"], "claims": a.get("claims", [])}
            g = spec.get(gid, {})
            texts = [g.get("title", "")] + list(g.get("steps", [])) + [x.get("label", "") for x in g.get("arrows", [])] + [x["text"] for x in g.get("callouts", [])]
            it["texts"] = [t for t in texts if t]
            tiers = {claims[i]["tier"] for i in it["claims"] if i in claims}
            if g.get("type") == "flow":
                shorts = [claims[i]["short"] for i in it["claims"] if i in claims]
                ok = all(any(s in t for t in g.get("steps", [])) for s in shorts)
                it.update(status="VERIFIED_SOURCE" if ok else "FAIL", why="each step carries its claim's short text" if ok else "a step does not match its claim text")
            elif g.get("type") == "geo" and g.get("arrows") and tiers <= {"original"}:
                c0 = claims.get(it["claims"][0], {})
                ok = str(c0.get("scale_km")) in g["arrows"][0]["label"]
                it.update(status="VERIFIED_SOURCE" if ok else "FAIL", why="arrow label equals the claim's announced length; the scale bar is computed from the grid" if ok else "arrow label differs from claim")
            else:
                frames = []
                for side in ("left", "right"):
                    if g.get(side):
                        gg = g[side]["geo"]
                        frames.append((gg["stack"], gg["center"], gg["width_km"]))
                if g.get("image"):
                    frames.append((g["image"]["stack"], g["image"]["center"], g["image"]["width_km"]))
                if frames:
                    image_assertion(it, frames)
                else:
                    it.update(status="NEEDS_VISUAL_REVIEW", why="no frame")
            finish(it)
        # 3) shots tied to claims without text (e.g. a wipe that illustrates a claim)
        if shot.get("claims") and g0.get("type") != "graphic":
            it = {"id": f"{shot['id']}:shot", "kind": "shot", "text": shot["info"], "shot": shot["id"], "claims": shot["claims"]}
            cam = shot.get("camera", {}).get("to")
            assets_ = []
            for l in shot["layers"]:
                for a_ in ([l.get("asset")] if l["type"] == "image" else [l.get("from"), l.get("to")] if l["type"] == "wipe" else []):
                    if a_ and a_ not in assets_:
                        assets_.append(a_)
            if cam and assets_:
                image_assertion(it, [(ep["assets"][a]["src"], cam["center"], cam["width_km"]) for a in assets_])
            else:
                it.update(status="NEEDS_VISUAL_REVIEW", why="no frame")
            finish(it)
    counts = {}
    for it in items:
        k = it["status"].split("_BY_")[0] if it["status"].startswith("REVIEWED") else it["status"]
        counts[k] = counts.get(k, 0) + 1
    res = {"schema": "yt-visualcheck/1", "overall": "FAIL" if counts.get("FAIL") else "NEEDS_VISUAL_REVIEW" if counts.get("NEEDS_VISUAL_REVIEW") else "OK", "counts": counts, "items": items}
    os.makedirs(os.path.join(root, "qa"), exist_ok=True)
    json.dump(res, open(os.path.join(root, "qa", "visual_claims.json"), "w"), indent=1, ensure_ascii=False)
    md = ["# Visual-claim check", "", f"Overall: **{res['overall']}** {counts}", "", "| item | claims | status | frame / why |", "|---|---|---|---|"]
    for it in items:
        md.append(f"| {it['id'][:60]} | {','.join(it['claims'])} | {it['status']} | {(it.get('frames') or [{}])[0].get('file', '')} {it.get('why', '')[:110]} |")
    md += ["", "Reviewing: look at each `frames` file, then add to qa/visual_review.json {item, frame_sha256, reviewer, verdict, note}. A review is bound to the frame hash."]
    open(os.path.join(root, "qa", "visual_claims.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    return res


def add_review(root, item, verdict, note, reviewer, frame=0):
    """Record a review bound to the CURRENT frame hash of that item (looked up from the last run); stale frames invalidate it."""
    rep = json.load(open(os.path.join(root, "qa", "visual_claims.json")))
    it = next((i for i in rep["items"] if i["id"] == item), None)
    if not it or not it.get("frames") or frame >= len(it["frames"]):
        raise ValueError(f"no reviewable frame {frame} for item {item!r}")
    if verdict not in ("supports", "does_not_support", "unclear") or len(note) < 20:
        raise ValueError("verdict must be supports|does_not_support|unclear and the note (what was seen) at least 20 characters")
    p = os.path.join(root, "qa", "visual_review.json")
    d = json.load(open(p)) if os.path.exists(p) else {"reviews": []}
    h = it["frames"][frame]["sha256"]
    d["reviews"] = [r for r in d["reviews"] if not (r["frame_sha256"] == h and sorted(r.get("claims", [])) == sorted(it["claims"]))] + [{"item": item, "frame": frame, "frame_sha256": h, "claims": sorted(it["claims"]), "reviewer": reviewer, "verdict": verdict, "note": note}]
    json.dump(d, open(p, "w"), indent=1, ensure_ascii=False)
    return {"status": "ok", "reviews": len(d["reviews"])}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check")
    rv = sub.add_parser("review")
    rv.add_argument("--item", required=True); rv.add_argument("--verdict", required=True); rv.add_argument("--note", required=True); rv.add_argument("--reviewer", default="agent", choices=["agent", "owner"]); rv.add_argument("--frame", type=int, default=0)
    a = ap.parse_args(argv)
    if a.cmd == "review":
        try:
            print(json.dumps(add_review(a.root, a.item, a.verdict, a.note, a.reviewer, a.frame)))
            return 0
        except (OSError, ValueError, KeyError) as e:
            print(json.dumps({"status": "error", "error": str(e)}))
            return 1
    try:
        r = run(a.root)
    except (OSError, KeyError, ValueError) as e:
        print(json.dumps({"status": "error", "error": f"{type(e).__name__}: {e}"}))
        return 1
    print(json.dumps({"status": r["overall"], "counts": r["counts"], "report": "qa/visual_claims.md"}, indent=1))
    return 0 if r["overall"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
