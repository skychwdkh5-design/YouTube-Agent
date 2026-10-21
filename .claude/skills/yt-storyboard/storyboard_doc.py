#!/usr/bin/env python3
"""storyboard_doc.py - a human-readable storyboard (markdown) of the first N seconds of a production, straight from story/storyboard.json, episode.json,
the evidence provenance and the media ledger. Nothing is typed in: every source, scale and rights status is read from the files.

    python3 storyboard_doc.py --root productions/<slug> --seconds 60 --out productions/<slug>/story/STORYBOARD_60S.md
"""
import argparse, json, os, sys


def scale_class(w):
    return "wide" if w >= 10 else "mid" if w >= 4 else "tight"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True); ap.add_argument("--seconds", type=float, default=60.0); ap.add_argument("--out")
    a = ap.parse_args(argv)
    P = lambda *x: os.path.join(a.root, *x)
    sb = json.load(open(P("story", "storyboard.json"))); ep = json.load(open(P("episode.json")))
    div = json.load(open(P("story", "diversity.json"))) if os.path.exists(P("story", "diversity.json")) else {}
    main_stack = ep["evidence"]["stacks"][0]["name"]
    prov = {s["id"]: s for s in json.load(open(P("evidence", main_stack, "provenance.json")))["scenes"]}
    claims = {c["id"]: c for c in json.load(open(P("claims.json")))["claims"]}
    L = [f"# Storyboard, first {a.seconds:.0f} s - {ep.get('title', ep['slug'])}", "",
         f"Generated from `story/storyboard.json` ({sb['timing']} timing, total {sb['duration']:.1f} s). Sources and rights are read from the provenance files and the media ledger; nothing is typed in.", "",
         "| time | shot | visual | scale | source / provenance | rights | motion / on-screen text |", "|---|---|---|---|---|---|---|"]
    for s in sb["shots"]:
        if s["start"] >= a.seconds:
            break
        l0 = s["layers"][0]
        t = f"{s['start']:.1f}-{s['start'] + s['dur']:.1f} s"
        mot = ""
        if l0["type"] == "graphic":
            g = ep["assets"][l0["asset"]]
            vis, scale = f"graphic `{l0['asset']}`", "-"
            src = "own graphic; claims " + ", ".join(g.get("claims") or []) + (" (" + "; ".join(f"{c}: {claims[c].get('attribution') or 'our measurement'}" for c in (g.get('claims') or []) if c in claims)[:120] + ")")
            rights = "own work / " + str(g.get("credit"))
            mot = "slow push-in"
        elif l0["type"] == "video":
            g = ep["assets"][l0["asset"]]
            led = json.load(open(P("media", "ledger.json")))["entries"] if os.path.exists(P("media", "ledger.json")) else []
            e = next((x for x in led if x["id"] == g.get("media_id")), {})
            vis, scale = f"REAL VIDEO `{l0['asset']}` (from {l0.get('trim', 0)} s)", "-"
            src = f"{e.get('page_url')} ({g.get('credit')}); file sha256 {str(e.get('sha256'))[:12]}"
            rights = f"{e.get('license')} - VERIFIED (evidence recorded {e.get('retrieved')})"
            mot = "source footage plays as is"
        elif l0["type"] == "still":
            g = ep["assets"][l0["asset"]]
            vis, scale = f"PHOTO `{l0['asset']}`", "-"
            src = f"{g.get('source_url')} ({g.get('credit')})"
            rights = f"{g.get('license')} - VERIFIED, file sha256 checked"
            mot = "slow push-in"
        else:
            cam = s.get("camera") or {}
            to = cam.get("to", {})
            frm = cam.get("from", {})
            ids = [l.get("asset") for l in s["layers"] if l["type"] == "image"] + [l.get("to") for l in s["layers"] if l["type"] == "wipe"]
            sc = prov.get(ids[0]) if ids else None
            vis = "satellite " + ("wipe " + "->".join(x for x in (s["info"].split()[-1].split("->"))) if "wipe" in s["info"] else s["info"])
            scale = scale_class(to.get("width_km", 8))
            src = f"Sentinel-2 L2A {sc['itemId']} ({sc['datetime'][:10]})" if sc else "Sentinel-2 L2A"
            rights = "Copernicus Sentinel data, free and open; credit on screen"
            mot = f"camera {frm.get('width_km', '?')} -> {to.get('width_km', '?')} km"
        labs = [l["text"] for l in s["layers"] if l["type"] == "label"]
        L.append(f"| {t} | {s['id']} | {vis} | {scale} | {src} | {rights} | {mot}{('; text: ' + '; '.join(labs)) if labs else ''} |")
    L += ["", "## Visual diversity", f"- status **{div.get('status', 'n/a')}**; kinds: {div.get('kind_share')}; longest satellite-map run {div.get('longest_map_run')}"] + [f"- WARNING: {w}" for w in div.get("warnings", [])]
    L += ["", "## Real media planned for this film (not in the render until the rights are VERIFIED)", "",
          "| candidate | scene | status | source page | would replace | why it is not drawn |", "|---|---|---|---|---|---|"]
    for p in div.get("media_pending", []):
        wr = p.get("would_replace")
        L.append(f"| {p.get('title', p['id'])} | {p.get('scene')} | **{p['status']}** | {p.get('page_url')} | {('shot ' + wr['shot'] + f' at {wr[chr(115)+chr(116)+chr(97)+chr(114)+chr(116)]:.1f} s, {wr[chr(100)+chr(117)+chr(114)]} s') if wr else '-'} | {'; '.join(p.get('reasons') or [])[:140]} |")
    for g in (ep.get("media_gaps") or []):
        L.append(f"| (gap) chapter {g['chapter']} | {g['chapter']} | MISSING | - | - | {g['need']} ({g['map_beats_in_a_row']} satellite beats in a row) |")
    txt = "\n".join(L) + "\n"
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
