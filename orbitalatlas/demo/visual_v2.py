"""Visual engine v2 demonstration (~18 s): real Landsat mosaics of the Great Salt Lake (EP003 stack), narration -> plan -> camera / graphics / captions.

    python3 -m orbitalatlas.demo.visual_v2 OUT.mp4 --stack productions/ep003-great-salt-lake/assets/landsat/stack_cal [--size 1920x1080] [--workers 4] [--proof]

What it shows (every element comes from the new modules; nothing is hand-timed - times come from the narration plan):
  * cinematic satellite zoom (camera_presets.smooth_zoom / snap_zoom / punch_zoom)           * animated territory highlight (RegionTint from a seeded water mask)
  * animated arrow with a 2.5D distance label + map pins (RouteArrow / RouteLabel / MarkerPin) * kinetic title, number count-up, year pop (kinetic)
  * word-synchronised captions, style chosen per phrase (captions A-E planner)                 * light wipe and flash dip transitions (transitions)
  * HUD frame, light sweep, neon grid, measured waveform (fx)                                  * documentary grade limited to `evidence_safe` on satellite pixels (grade)
Narration: free flite TEST voice with measured word timings (NOT the channel voice, no paid TTS). Output is silent-proof quality unless --audio.
Not copyrighted material: no frame of the two reference videos is used."""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "yt-geo"))
from orbitalatlas import camera_presets as CP, captions as C, fx, grade, kinetic as K, regions, semantic, testvoice, transitions as TR  # noqa: E402
from orbitalatlas.layers import Scene, SourceChip  # noqa: E402
from orbitalatlas.sequence import Program, Sequence, Shot, render_video  # noqa: E402
import geostack as G  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
TEXT = ("In 1985, the Great Salt Lake filled this basin. By July 2022, it had fallen to 4,190.2 feet. "
        "About 80 kilometers from Salt Lake City, a causeway splits it in two. But dust from the drying lake now worsens regional air pollution.")
SAY = {"1985,": "nineteen eighty five", "2022,": "twenty twenty two", "4,190.2": "four thousand one hundred ninety point two", "80": "eighty"}
# the verified facts behind the narration: story/claims.json C1 (4,190.2 ft July 2022), C12 (causeway 1959 divides the lake), C16 (NASA: dust worsens regional air pollution);
# "About 80 kilometers" is DERIVED here from the two pin coordinates (haversine, printed by --report), not a sourced claim.
PINS = {"Salt Lake City": (-111.89, 40.76), "causeway": (-112.65, 41.226)}
VIEWS = {"whole": ((-112.5, 41.2), 228), "whole_in": ((-112.45, 41.15), 190), "east": ((-112.1, 40.88), 75), "pair": ((-112.27, 40.99), 125)}
SEEDS = {"1985": [(-112.7, 41.4), (-112.4, 41.0), (-112.2, 40.85), (-112.1, 41.05), (-112.3, 41.15)], "2022": [(-112.8, 41.33), (-112.35, 40.9), (-112.3, 41.0)]}
BOX = ((-113.15, 41.78), (-111.96, 40.62))


def haversine_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


class Stack:
    def __init__(self, d):
        self.d = d; self.g = json.load(open(os.path.join(d, "grid.json")))
    def px(self, lon, lat):
        x, y = G.lonlat_to_utm(lon, lat, self.g["epsg"]); return ((float(x) - self.g["x0"]) / self.g["pixel_m"], (self.g["y_top"] - float(y)) / self.g["pixel_m"])
    def height(self, width_km): return width_km * 1000.0 / self.g["pixel_m"] * 9 / 16
    def view(self, name):
        (lon, lat), w = VIEWS[name]; return self.px(lon, lat), self.height(w)
    def image(self, y): return Image.open(os.path.join(self.d, f"y{y}.png")).convert("RGB")
    def mask(self, y, img, f=4):
        small = np.asarray(img.resize((img.width // f, img.height // f), Image.LANCZOS))
        (a, b), (c, d) = self.px(*BOX[0]), self.px(*BOX[1])
        m = regions.seeded_region(small, [(self.px(*s)[0] / f, self.px(*s)[1] / f) for s in SEEDS[y]], box=(a / f, b / f, c / f, d / f), close=2, fill_holes=False, max_hole_px=700)
        return regions.to_mask_image(m, f), 1.0 / f, float(m.sum() * (self.g["pixel_m"] * f) ** 2 / 1e6)


def first(plan, kind, **kw):
    return next(e for e in plan["events"] if e["kind"] == kind and all(e.get(k) == v for k, v in kw.items()))


def build(stack_dir, workdir, size=(1920, 1080), tempo=1.45, log=print):
    st = Stack(stack_dir); os.makedirs(workdir, exist_ok=True)
    words = [dict(text=t, **({"say": SAY[t]} if t in SAY else {})) for t in TEXT.split()]
    words, info = testvoice.synth(words, os.path.join(workdir, "narration_test.wav"), os.path.join(workdir, "words"), tempo=tempo)
    plan = semantic.plan([{k: v for k, v in w.items() if k != "say"} for w in words], places={"Great Salt Lake": {}, "Salt Lake City": {}, "causeway": {}}, mode="long", source=info["source"], max_events_per_10s=7)
    D = info["duration"]; W = lambda i: plan["words"][i]
    ev_by = lambda kind, **kw: [e for e in plan["events"] if e["kind"] == kind and all(e.get(k) == v for k, v in kw.items())]
    t_lake = ev_by("place", place="Great Salt Lake")[0]["t"]; t_y85 = ev_by("year")[0]["t"]
    t_july = next(w["start"] for w in plan["words"] if w["text"] == "July"); t_num = ev_by("number")
    t_feet = next(e for e in plan["events"] if e["kind"] == "number" and "4,190" in e["text"])
    t_80 = next(e for e in plan["events"] if e["kind"] == "number" and e["text"] == "80")
    t_slc = ev_by("place", place="Salt Lake City")[0]["t"]; t_cause = ev_by("place", place="causeway")[0]["t"]
    t_but = ev_by("revelation")[0]["t"]
    d_wipe, d_flash = 0.7, 0.34
    b1, b2 = t_july - 0.35, t_but - 0.12                                   # transition centres: before 'July 2022' and at 'But'
    starts = [0.0, b1 - d_wipe / 2, b2 - d_flash / 2 - (0.0)]
    # ---- shot 1: 1985 ---------------------------------------------------------------------------------------------------
    img85, img22 = st.image("1985"), st.image("2022")
    m85, ms85, a85 = st.mask("1985", img85); m22, ms22, a22 = st.mask("2022", img22)
    (cw, hw), (ci, hi), (ce, he), (cp, hp) = st.view("whole"), st.view("whole_in"), st.view("east"), st.view("pair")
    full_h = st.g["width"] * 9 / 16 * 0.99; cfull = (st.g["width"] / 2, st.g["height"] * 0.5)   # whole image width fills the frame (no pillarbox)
    s1_len = b1 + d_wipe / 2
    k1 = CP.join(CP.smooth_zoom(0.0, 2.6, cfull, full_h, cw, hw), CP.smooth_zoom(2.6, max(0.5, s1_len - 2.6), cw, hw, ci, hi))
    L1 = lambda t: t - starts[0]
    o1 = [fx.RegionTint(m85, L1(t_lake), color=fx.AMBER, settle_alpha=0.12, mask_scale=ms85, source="seeded water mask on the 1985 Landsat mosaic (orbitalatlas.regions)", validation=f"annotation only; mask area about {a85:,.0f} km2 is a display shape, not a measurement", out_t=L1(b1 - 0.1)),
          SourceChip((0.03, 0.935), "LANDSAT 5 · USGS · JUNE 1985 · MOSAIC, DISPLAY GRADE", 0.2)]
    sc1 = grade.Graded(Scene(img85, k1, size, overlays=o1, name="y1985", clamp=False), "evidence_safe", evidence=True)
    # ---- shot 2: 2022 -----------------------------------------------------------------------------------------------------
    s2_start = starts[1]; s2_end = b2 + d_flash / 2; s2_len = s2_end - s2_start; L2 = lambda t: t - s2_start
    t_snap = t_80["t"] - 0.25
    k2 = CP.join(CP.hold(0.0, ci, hi), CP.snap_zoom(L2(t_snap), ci, hi, cp, hp, dur=0.6), CP.creep(L2(t_snap) + 0.6, max(0.5, s2_len - L2(t_snap) - 0.6), cp, hp, 0.04))
    arrow = fx.RouteArrow(st.px(*PINS["Salt Lake City"]), st.px(*PINS["causeway"]), L2(t_80["t"] + 0.1), dur=max(1.2, t_cause + 0.5 - t_80["t"]), bend=-0.2, label="80 KM",
                          source="pins: Salt Lake City 40.76 N 111.89 W; causeway midpoint 41.226 N 112.65 W (checked on the 2022 mosaic)", validation="presentation arrow between two verified anchors, not a measured route; 80 km is the great-circle distance between the pins",
                          out_t=L2(s2_end - 0.2))
    o2 = [fx.RegionTint(m22, L2(starts[1] + d_wipe), color=fx.CYAN, settle_alpha=0.10, mask_scale=ms22, source="seeded water mask on the 2022 Landsat mosaic", validation=f"annotation only; about {a22:,.0f} km2 display shape", out_t=L2(t_snap)),
          fx.MarkerPin(st.px(*PINS["Salt Lake City"]), L2(t_slc), label="Salt Lake City", source="coordinates 40.76 N, 111.89 W", out_t=L2(s2_end - 0.25)),
          fx.MarkerPin(st.px(*PINS["causeway"]), L2(t_cause), label="Causeway", source="causeway midpoint, checked on the mosaic", out_t=L2(s2_end - 0.25)),
          arrow, fx.RouteLabel(arrow, L2(t_80["t"] + 0.1 + max(1.2, t_cause + 0.5 - t_80["t"]) * 0.55), px=70, out_t=L2(s2_end - 0.25)),
          SourceChip((0.03, 0.935), "LANDSAT 8, 9 · USGS · JULY 2022 · MOSAIC, DISPLAY GRADE", 0.2)]
    sc2 = grade.Graded(Scene(img22, k2, size, overlays=o2, name="y2022", clamp=False), "evidence_safe", evidence=True)
    # ---- shot 3: dust -----------------------------------------------------------------------------------------------------
    s3_start = starts[2]; s3_len = D - s3_start; L3 = lambda t: t - s3_start
    k3 = CP.join(CP.hold(0.0, ce, he * 1.18), CP.punch_zoom(L3(t_but + 0.15), ce, he * 1.18, 0.82, 0.14, 0.05, max(1.0, s3_len)))
    o3 = [fx.HudFrame((0.04, 0.06, 0.96, 0.775), L3(t_but + 0.1), color=fx.CYAN, label="EAST SHORE · EXPOSED LAKE BED", dur=0.7),
          fx.MarkerPin(st.px(-112.1, 40.97), L3(t_but + 0.5), label="Farmington Bay", source="coordinates 40.97 N, 112.1 W (EP003 stack pin)"),
          SourceChip((0.03, 0.935), "LANDSAT 8, 9 · USGS · JULY 2022 · MOSAIC, DISPLAY GRADE", 0.2)]
    sc3 = grade.Graded(Scene(img22, k3, size, overlays=o3, name="dust", clamp=False), "evidence_safe", evidence=True)
    seq = Sequence([Shot(sc1, s1_len), Shot(sc2, s2_len), Shot(sc3, s3_len)], [TR.LightWipe(d_wipe), TR.FlashDip(d_flash, color=(255, 255, 255), peak=0.8)])
    # ---- global overlays: captions, title, kinetic facts, grid/sweep, waveform -----------------------------------------------
    cards = C.make_cards(plan["words"]); styles = list(plan["styles"])
    caps = C.WordCaptions(cards, styles, source=info["source"])
    env = testvoice.envelope(os.path.join(workdir, "narration_test.wav"))
    over = [fx.NeonGrid(0.0, 2.6, color=fx.PURPLE, alpha=0.22, flat=True, spacing=0.09, fade=0.6),
            K.KineticTitle("GREAT SALT LAKE", "FORTY YEARS FROM ORBIT", 0.25, 2.7, xy=(0.06, 0.10)),
            fx.LightSweep(0.55, 1.0, strength=0.20),
            K.StatPop("1985", t_y85, xy=(0.84, 0.16), px=0.12, hold=1.3, glow_color=fx.CYAN, group="year1985"),
            K.StatPop("JULY 2022", t_july, xy=(0.80, 0.16), px=0.085, hold=1.2, glow_color=fx.CYAN, group="year2022"),
            K.StatPop("4,190.2 FEET", t_feet["t"] + 0.05, xy=(0.5, 0.36), px=0.115, hold=1.5, color=(255, 214, 120), glow_color=fx.AMBER, count_up=True, group="stat_feet"),
            fx.Waveform((0.62, 0.90, 0.96, 0.95), t_but, D, samples=env[int(t_but * 30):] if len(env) > int(t_but * 30) else env, color=fx.PURPLE, fps=30.0),
            caps]
    prog = Program(seq, over)
    return prog, dict(plan=plan, info=info, areas_km2=dict(y1985=round(a85), y2022=round(a22)), distance_km=round(haversine_km(PINS["Salt Lake City"], PINS["causeway"]), 1), duration=D,
                      times=dict(lake=t_lake, y1985=t_y85, july=t_july, feet=t_feet["t"], eighty=t_80["t"], slc=t_slc, causeway=t_cause, but=t_but, wipe=b1, flash=b2))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out"); ap.add_argument("--stack", required=True); ap.add_argument("--size", default="1920x1080"); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--workdir", default=None); ap.add_argument("--stills", default=None, help="comma-separated times (s): write PNG frames next to OUT instead of a video")
    ap.add_argument("--report", action="store_true"); ap.add_argument("--qa", action="store_true", help="run overlay + video QA after rendering (TECHNICALLY_VALID checks only)"); ap.add_argument("--audio", action="store_true", help="mux the flite test narration into the file")
    a = ap.parse_args(argv)
    size = tuple(int(x) for x in a.size.split("x")); wd = a.workdir or os.path.join(os.path.dirname(os.path.abspath(a.out)), "visual_v2_work")
    prog, meta = build(a.stack, wd, size)
    json.dump(dict(schedule=prog.schedule(), meta={k: v for k, v in meta.items() if k != "plan"}, plan=dict(meta["plan"], words=[{k: v for k, v in w.items()} for w in meta["plan"]["words"]])), open(os.path.join(wd, "plan.json"), "w"), indent=1, default=str)
    if a.report: print(json.dumps({k: v for k, v in meta.items() if k not in ("plan",)}, indent=1, default=str)); print(meta["plan"]["styles"], [ (e["kind"], e["t"], e["text"]) for e in meta["plan"]["events"]])
    if a.stills:
        base = os.path.splitext(a.out)[0]
        for ts in a.stills.split(","):
            prog.render(float(ts)).save(f"{base}_{float(ts):05.2f}.png"); print("wrote", f"{base}_{float(ts):05.2f}.png")
        return
    n = render_video(prog, a.out, 30, a.workers, audio=os.path.join(wd, "narration_test.wav") if a.audio else None)
    if a.qa:
        from orbitalatlas import qa as QA
        ov = prog.check_overlays(0.1) + [i for sh in prog.shots for i in QA.check_overlays(sh.scene.scene if hasattr(sh.scene, "scene") else sh.scene)]
        rep = QA.run_video(a.out, schedule=prog.schedule(), problems=prog.problems, holds=[(0.0, 0.5)])
        print("overlay issues:", len(ov), ov[:6]); print("video QA:", json.dumps(rep, default=str)[:900])
        json.dump(dict(overlay_issues=ov, video=rep), open(os.path.join(wd, "qa.json"), "w"), indent=1, default=str)
    print(f"{n} frames -> {a.out}  duration {prog.duration:.2f}s  timing={meta['info']['source']} ({meta['info']['voice']})")


if __name__ == "__main__":
    main()
