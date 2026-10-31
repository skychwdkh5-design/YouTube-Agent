#!/usr/bin/env python3
"""EP008 full DRAFT (temporary Kokoro voice - not for release). 1920x1080, 30 fps, H.264 High + AAC.

    python3 draft.py --media /home/claude/ep008-media --render --confirm [--scenes s01,s02] [--jobs 2]

Picture is cut on the voice: every shot is anchored to a sentence of voice_temp/timing.json (anchor i.f = sentence i
start + f of its length). Media: NASA stills/clips from draft release ep008-originals (research/media.json); graphics from
graphics.py; NASA con-ops graphic shown as large fragments (never above native resolution) with the narrated item lit.
Mission chips on every picture (owner rule 2026-10-31): blue = Artemis II (flown), gold = Artemis III plan, white = hardware.
Writes draft/EP008_draft_v1.mp4 + .srt + .timeline.json. Never uploads.
"""
import argparse, json, os, subprocess, tempfile
from multiprocessing import Pool
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw
import graphics as g
import hook20 as hk

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, GAP, TAIL = 1920, 1080, 30, 0.35, 1.2
GOLD, WHITE, RED = (255, 210, 30), (255, 255, 255), (229, 50, 45)
A2, A3, HW = "a2", "a3plan", "a3hw"
V1, V2, V3, V4, V5 = "v1_a2_launch_causeway.mp4", "v2_a2_orion_window_reentry.mp4", "v3_a2_splashdown.mp4", "v4_a3_booster_stacking.mp4", "v5_a3_rs25_to_workstand.mp4"
LUNAR, EARTHSET, SPACER = hk.LUNAR, hk.EARTHSET, hk.SPACER
P = lambda f, b0, b1, chip, credit, texts=(): ("photo", f, b0, b1, chip, credit, list(texts))
C = lambda f, start, chip, credit, texts=(): ("clip", f, start, chip, credit, list(texts))
G = lambda fn, *args, chip=None, **kw: ("g", fn, args, chip, kw)
CO = lambda view, boxes, title=None, sub=None: ("conops", view, boxes, title, sub)
T = lambda txt, size=72, col=GOLD, xy=(70, 60), t_in=0.0: (txt, size, col, xy, t_in)
A2C = "NASA · ARTEMIS II PHOTO, APR 6, 2026"

SHOTS = {
    "s01": [(0, ("lunar_open",)), (1, G("d_orbit_vs_moon", chip=A3))],
    "s02": [(0, P(EARTHSET, (0.08, 0.18, 0.88, 0), (0.13, 0.20, 0.90, 0), A2, A2C, [T("ARTEMIS II · APRIL 2026", 64), T("AROUND THE MOON", 52, WHITE, (70, 140), 0.4)])),
            (1, G("d_sls_stack")), (3, P(SPACER, (0.14, 0.08, 0.86, 0), (0.24, 0.16, 0.76, 0), HW, "NASA/SAM LOTT · MARSHALL, JULY 2026",
                                       [T("ARTEMIS III SPACER", 56, WHITE), T("NO ENGINE", 120, GOLD, (70, 130))]))],
    "s03": [(0, G("d_timeline2")),
            (1, CO((0.0, 0.0, 1.0), ["leo"], "14 DAYS IN LOW EARTH ORBIT")),
            (1.38, CO((0.30, 0.07, 0.5), ["bm_ops", "ss_ops"], "2 MOON LANDERS", "test articles from Blue Origin and SpaceX")),
            (1.72, CO((0.30, 0.07, 0.5), ["bm_ops"], "THE TEST: DOCKING", "must work before any landing")),
            (2, P("a2_hertzsprung_art002e012093.jpg", (0.05, 0.10, 0.85, 0), (0.12, 0.16, 0.80, 0), A2, A2C,
                  [T("FIRST LANDING: ARTEMIS IV"), T("PLANNED FOR 2028", 56, WHITE, (70, 150), 0.3)]))],
    "s04": [(0, C(V1, 27.0, "a2vid", "NASA · ARTEMIS II LAUNCH, APR 1, 2026", [T("ARTEMIS II · 10 DAYS")])),
            (1.3, P(EARTHSET, (0.20, 0.25, 0.80, 0), (0.25, 0.30, 0.78, 0), A2, A2C, [T("APR 6 · LUNAR FLYBY")])),
            (1.7, C(V3, 152.0, "a2vid", "NASA · ARTEMIS II SPLASHDOWN, APR 10, 2026", [T("APR 10 · SPLASHDOWN")])),
            (2, G("d_timeline2", chip=None)),
            (3, P("artemis_cadence_infographic_feb2026.jpg", (0.0, 0.0, 1.0, 0), (0.05, 0.05, 0.90, 0), A3, "NASA GRAPHIC, FEB 27, 2026",
                  [T("FEB 27, 2026", 64)])),
            (4, G("d_plan_swap", chip=A3)),
            (6, G("card", "AFTER THE FIRST LANDING", ["At least one landing every year (NASA plan)"], "Source: NASA, Feb 27, 2026", chip=A3)),
            (7, C(V5, 195.0, "a3hw", "NASA · ARTEMIS III RS-25, VAB, AUG 2026", [T("NASA'S REASONING", 64)])),
            (8.35, C(V4, 61.0, "a3hw", "NASA · ARTEMIS III BOOSTER STACKING, SEP 2026",
                     [T("SAME CONFIGURATION AS FLOWN", 60), T("FLY MORE OFTEN", 60, GOLD, (70, 140), 1.2), T("STEP BY STEP", 60, GOLD, (70, 220), 2.4)])),
            (9, G("quote", "Standardizing vehicle configuration, increasing\nflight rate and progressing through objectives\nin a logical, phased approach, is how we\nachieved the near-impossible in 1969.",
                  "JARED ISAACMAN, NASA ADMINISTRATOR", "Source: NASA, Feb 27, 2026"))],
    "s05": [(0, C(V5, 108.0, "a3hw", "NASA · ARTEMIS III RS-25 ENGINE, VAB, AUG 2026", [T("NOT A PAPER MISSION", 64), T("4 RS-25 ENGINES AT KENNEDY · JULY", 50, WHITE, (70, 140), 2.0)])),
            (2, P("a3_orion_joined_wp_ksc-20260730-ph-as01-6583.jpg", (0.0, 0.10, 1.0, 0), (0.0, 0.42, 1.0, 0), HW, "NASA/AMANDA STEVENSON · KENNEDY, JULY 2026",
                  [T("ARTEMIS III ORION · JOINED LATE JULY", 60)])),
            (3, C(V4, 15.0, "a3hw", "NASA · ARTEMIS III BOOSTER STACKING, SEP 2026", [T("BOOSTERS STACKED", 64)])),
            (3.55, ("portrait", "a3_srb_nosecones_large.jpg", HW, "NASA/CORY S HUSTON · VAB, SEP 30, 2026", [T("SEPT 30: NOSE CONES ON", 60)])),
            (4, P("a3_solar_array_large.jpg", (0.0, 0.0, 1.0, 0), (0.0, 0.25, 1.0, 0), HW, "NASA/AMANDA STEVENSON · KENNEDY, AUG 2026",
                  [T("250+ ARTEMIS II ORION PARTS REUSED", 56)])),
            (4.5, G("card", "FASTER", ["Reused parts: some installation ~3 months earlier", "Launch tower turnaround: nearly 50% faster"], "Source: NASA, Aug 5, 2026", chip=HW)),
            (5, C(V1, 2.0, "a2vid", "NASA · ARTEMIS II ON THE PAD, APR 1, 2026", [T("LAUNCH TOWER", 64), T("TURNAROUND ~50% FASTER (NASA)", 50, WHITE, (70, 140), 0.8)])),
            (6, G("d_stage_to_a4", chip=A3))],
    "s06": [(0, G("card", "THE ARTEMIS III CREW", ["Randy Bresnik · NASA", "Andre Douglas · NASA", "Frank Rubio · NASA", "Luca Parmitano · ESA"],
                  "Source: NASA, Jun 9 and Oct 13, 2026", "NAMES ONLY · NO PORTRAITS", chip=A3)),
            (1, G("card", "TRAINING · SEPT 2026", ["Navy helicopter crews, off San Diego", "Hoisted out of the water after splashdown"],
                  "Source: NASA status update, Oct 13, 2026", chip=A3)),
            (2, G("card", "MORE TRAINING", ["Escaping a capsule underwater", "Orange Orion survival suits", "Tasting nearly 200 space foods"],
                  "Source: NASA status update, Oct 13, 2026", chip=A3)),
            (3, G("d_distance", chip=A3))],
    "s07": [(0, CO((0.0, 0.0, 1.0), ["r_ng", "r_sls", "r_ss"], "3 LAUNCHES")),
            (1, CO((0.0, 0.43, 0.5), ["r_ng"], "LAUNCH 1", "Blue Moon test article, Blue Origin")),
            (2, CO((0.0, 0.07, 0.5), ["bm_check"], "WAITS UP TO 30 DAYS", "in a circular orbit")),
            (3, CO((0.0, 0.43, 0.5), ["r_sls"], "LAUNCH 2", "the crew, on SLS")),
            (4, CO((0.40, 0.40, 0.5), ["r_ss"], "LAUNCH 3: STARSHIP", "later - built for a shorter stay in space"))],
    "s08": [(0, G("d_orbits", 1, chip=A3)), (2, G("d_orbits", 2, chip=A3)), (3, G("d_orbits", 3, chip=A3)), (4, G("d_orbits", 4, chip=A3))],
    "s09": [(0, G("d_dock", "side", chip=A3)),
            (2, CO((0.30, 0.07, 0.5), ["bm_ops"], "DOCK 1: BLUE MOON", "Orion's software flies both spacecraft")),
            (3, G("d_dock", "hatch", chip=A3)),
            (5, CO((0.30, 0.07, 0.5), ["bm_ops"], "A FIRST FOR NASA", "crewed evaluation of a commercial lunar lander")),
            (6, G("d_clock", chip=A3)),
            (7, G("card", "RIDING ALONG", ["A spacesuit mass simulator", "Wired with sensors", "Reports conditions inside the cabin"], "Source: NASA, Jul 15, 2026", chip=A3))],
    "s10": [(0, CO((0.40, 0.40, 0.5), ["r_ss"], "DOCK 2: STARSHIP", "test vehicle: 171 ft / 52 m")),
            (2, CO((0.5, 0.07, 0.5), ["ss_ops"], "171 FT · 52 M", "docking port in its nose")),
            (3, G("d_dock", "nose", chip=A3)),
            (4, G("d_dock", "timer", chip=A3)),
            (5, CO((0.5, 0.07, 0.5), ["ss_ops"], "TESTS STILL BEING DEFINED", "NASA and SpaceX, Jul 2026"))],
    "s11": [(0, CO((0.5, 0.07, 0.5), ["tests"], "UP TO 5 EXTRA DAYS", "Orion tests")),
            (1, G("card", "EXTRA TESTS", ["Orion survival suit checks", "Docking sensor tests", "Acoustic and thermal measurements", "How the crew lives and works on board"],
                  "Source: NASA flight profile, Oct 23, 2026", chip=A3)),
            (2, CO((0.5, 0.35, 0.5), ["reentry", "splash"], "~14 DAYS, THEN HOME", "splashdown in the Pacific, off California")),
            (2.4, C(V2, 580.0, "a2vid", "NASA · ARTEMIS II, VIEW FROM ORION'S WINDOW, APR 10, 2026", [T("SAME OCEAN AS ARTEMIS II", 60)])),
            (2.7, C(V3, 154.0, "a2vid", "NASA · ARTEMIS II SPLASHDOWN, APR 10, 2026", [T("ARTEMIS II · PACIFIC · APR 10", 60)]))],
    "s12": [(0, G("card", "WHY A WHOLE MISSION?", [], "", big="?")),
            (1, G("quote", "Every piece of this mission in Earth orbit\nis designed to reduce risk before we put\nastronauts back on the Moon.",
                  "JEREMY PARSONS, NASA ARTEMIS PROGRAM MANAGER", "Source: NASA, Oct 23, 2026")),
            (3, CO((0.0, 0.0, 1.0), ["r_ng", "r_sls", "r_ss"], "3 SPACECRAFT · 3 ROCKETS", "\"something NASA has never attempted\"")),
            (4, G("d_handoff", chip=A3)),
            (7, P("a2_tiny_earth_art002e009284.jpg", (0.05, 0.05, 0.95, 0), (0.15, 0.12, 0.85, 0), A2, A2C, [T("ARTEMIS II: SEVERAL DAYS HOME", 64)])),
            (9, G("d_hours")),
            (10, G("d_orbit_vs_moon", chip=A3))],
    "s13": [(0, G("d_apollo"))],
    "s14": [(0, C(V4, 75.0, "a3hw", "NASA · ARTEMIS III BOOSTER STACKING, SEP 2026", [T("LAUNCH: 2027", 72), T("NO DATE ANNOUNCED", 56, WHITE, (70, 150), 0.8)])),
            (3, ("portrait", "a3_srb_nosecones_large.jpg", HW, "NASA/CORY S HUSTON · VAB, SEP 30, 2026", [T("FUELING TEST AT THE PAD: AHEAD", 56)])),
            (4, CO((0.30, 0.07, 0.5), ["bm_ops", "ss_ops"], "ARTEMIS IV LANDER?", "NASA hasn't said which"))],
    "s15": [(0, G("d_orbit_vs_moon", chip=A3)),
            (1, P("a2_earthrise_art002e021278.jpg", (0.05, 0.10, 0.90, 0), (0.12, 0.15, 0.85, 0), A2, A2C, [T("IF BOTH DOCKINGS WORK", 64)])),
            (2, P(LUNAR, hk.COVER_BOX, (0.04, 0.03, 0.60, 0), A2, A2C, [T("ARTEMIS IV: THE LANDING (PLANNED 2028)", 60), T("ARTEMIS III: THE TEST", 72, WHITE, (70, 140), 2.0)]))],
}


def plan():
    t = json.load(open(os.path.join(HERE, "voice_temp", "timing.json")))
    shots, lines, starts, at = [], [], {}, 0.0
    order = sorted(SHOTS)
    for sid in order:
        sc = t[sid]; starts[sid] = round(at, 3); sents = sc["sentences"]
        def anchor(a):
            i = int(a); f = a - i; s_ = sents[i]
            return at + s_["start"] + f * (s_["end"] - s_["start"]) - (0.08 if f == 0 and a > 0 else 0)
        nxt = at + sc["dur"] + GAP
        end_scene = nxt if sid != order[-1] else nxt + TAIL
        sl = SHOTS[sid]
        for k, (a, spec) in enumerate(sl):
            a0 = at if k == 0 else anchor(a)
            a1 = end_scene if k == len(sl) - 1 else anchor(sl[k + 1][0])
            shots.append(dict(scene=sid, start=round(a0, 3), end=round(a1, 3), spec=spec))
        lines += [(at + x["start"], at + x["end"], x["text"]) for x in sents]
        at = nxt
    return shots, lines, starts, round(at + TAIL, 3)


def _clip_reader(path, start, dur):
    vf = ("fps=30,split[a][b];[a]scale=1920:1080,boxblur=30:4,eq=brightness=-0.12[bg];[b]scale=1920:-2[fg];"
          "[bg][fg]overlay=(W-w)/2:(H-h)/2")
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i", path, "-t", str(dur + 0.2),
                          "-filter_complex", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    last = None
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        last = Image.frombytes("RGB", (W, H), b); yield last
    while True:
        yield last


def overlays(im, texts, tl):
    for txt, size, col, xy, t_in in texts:
        a = min(1, max(0, (tl - t_in) / 0.25))
        if a > 0:
            im = g.text_on(im, xy, txt, size, col, alpha=a)
    return im


def render_frame(spec, u, tl, dur, media, state):
    k = spec[0]; m = lambda f: os.path.join(media, f)
    if k == "lunar_open":
        im = g.photo(m(LUNAR), u, hk.COVER_BOX, (0.05, 0.03, 0.60, 0.515), A2C)
        im = g.chip(im, "a2")
        a = min(1, max(0, (tl - 0.2) / 0.25))
        if a > 0:
            im = g.text_on(im, (W * 0.47, H * 0.47), "ARTEMIS III PLAN:", 70, WHITE, alpha=a)
            im = g.text_on(im, (W * 0.47, H * 0.55), "LAND ON THE MOON", 110, GOLD, alpha=a)
        kk = min(1, max(0, (tl - (dur - 0.35)) / 0.25))
        if kk > 0:
            tw = g.font(110).getlength("LAND ON THE MOON")
            ImageDraw.Draw(im).line([(W * 0.465, H * 0.64), (W * 0.465 + (tw + 20) * kk, H * 0.64 - 50 * kk)], fill=RED, width=16)
        return im
    if k == "photo":
        _, f, b0, b1, chip, credit, texts = spec
        return g.chip(overlays(g.photo(m(f), u, b0, b1, credit), texts, tl), chip)
    if k == "portrait":
        _, f, chip, credit, texts = spec
        return g.chip(overlays(g.portrait(m(f), u, credit), texts, tl), chip)
    if k == "clip":
        _, f, start, chip, credit, texts = spec
        if state.get("clip") is None:
            state["clip"] = _clip_reader(m(f), start, dur)
        im = next(state["clip"]).copy()
        ImageDraw.Draw(im).text((W - 40, H - 34), credit, font=g.font(24, g.INTER), fill=WHITE, anchor="rs", stroke_width=2, stroke_fill=(0, 0, 0))
        return g.chip(overlays(im, texts, tl), chip)
    if k == "conops":
        _, view, boxes, title, sub = spec
        return g.chip(g.conops(m(g.CONOPS), u, view, boxes, title, sub), "a3plan")
    if k == "g":
        _, fn, args, chip, kw = spec
        im = getattr(g, fn)(u, *args, **kw)
        return g.chip(im, chip) if chip else im


def render_range(job):
    i0, i1, shots, caps, media, out = job
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
                           "-g", "60", out], stdin=subprocess.PIPE)
    cur, state = None, {}
    for i in range(i0, i1):
        t = i / FPS
        sh = next((s for s in shots if s["start"] <= t < s["end"]), shots[-1])
        if sh is not cur:
            cur, state = sh, {}
        dur = sh["end"] - sh["start"]
        im = render_frame(sh["spec"], min(1, (t - sh["start"]) / dur), t - sh["start"], dur, media, state)
        if t > END - 0.6:
            im = Image.blend(im, Image.new("RGB", (W, H)), min(1, (t - END + 0.6) / 0.6))
        pr.stdin.write(hk.caption(im, t, caps).tobytes())
    pr.stdin.close(); pr.wait()
    return out


def audio(starts, n_s, sr=24000):
    n = int(n_s * sr); mix = np.zeros(n, np.float32)
    for sid, at in starts.items():
        v, sr_ = sf.read(os.path.join(HERE, "voice_temp", sid + ".wav"), dtype="float32")
        i = int(at * sr); mix[i: i + len(v)] += v[: max(0, n - i)]
    shots_hook = [s for s in SHOTS_PLAN if s["scene"] in ("s01", "s02")]
    cut1, cut2, cut3 = shots_hook[1]["start"], shots_hook[3]["start"], shots_hook[4]["start"]
    hk.END = starts["s03"]
    mix[: int(starts["s03"] * sr)] += hk.sfx(sr, cut1, cut2, cut3, int(starts["s03"] * sr))
    x = np.arange(n) / sr                                                          # original synthesised pad, under the voice
    pad = sum(np.sin(2 * np.pi * f * x) * (0.5 + 0.5 * np.sin(2 * np.pi * x / p_)) for f, p_ in ((110, 9), (164.8, 13), (220, 11), (329.6, 17)))
    env = np.clip((x - starts["s03"]) / 3, 0, 1) * np.clip((n_s - x) / 2, 0, 1)
    mix += 0.012 * pad.astype(np.float32) * env
    return mix, sr


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--media", required=True); ap.add_argument("--render", action="store_true")
    ap.add_argument("--confirm", action="store_true"); ap.add_argument("--jobs", type=int, default=2); ap.add_argument("--scenes", default=""); ap.add_argument("--reuse", default="")
    a = ap.parse_args()
    SHOTS_PLAN, lines, starts, END = plan()
    caps = hk.chunks(lines)
    os.makedirs(os.path.join(HERE, "draft"), exist_ok=True)
    json.dump({"end": END, "starts": starts, "shots": [{**s, "spec": [str(x) for x in s["spec"][:2]]} for s in SHOTS_PLAN]},
              open(os.path.join(HERE, "draft", "EP008_draft_v1.timeline.json"), "w"), indent=1)
    if not (a.render and a.confirm):
        print(json.dumps({"end": END, "shots": len(SHOTS_PLAN), "note": "add --render --confirm"})); raise SystemExit
    want = set(filter(None, a.scenes.split(",")))
    tmp = a.reuse or tempfile.mkdtemp(dir=os.path.join(HERE, "draft"))
    ids = sorted(starts); bounds = [starts[s] for s in ids] + [END]
    jobs = []
    for k, sid in enumerate(ids):
        if want and sid not in want:
            continue
        jobs.append((round(bounds[k] * FPS), round(bounds[k + 1] * FPS), SHOTS_PLAN, caps, a.media, os.path.join(tmp, f"{sid}.mp4")))
    def complete(j):                                       # --reuse: keep segments that already have every frame
        r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets",
                            "-of", "csv=p=0", j[5]], capture_output=True, text=True)
        return r.stdout.strip() == str(j[1] - j[0])
    todo = [j for j in jobs if not (a.reuse and os.path.exists(j[5]) and complete(j))]
    with Pool(a.jobs) as pool:
        pool.map(render_range, todo, chunksize=1)
    bad = [j[5] for j in jobs if not complete(j)]
    if bad:
        raise SystemExit(f"incomplete segments: {bad}")
    parts = [j[5] for j in jobs]
    tag = "partial_" + "_".join(sorted(want)) if want else "EP008_draft_v1"
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    vid = os.path.join(tmp, "v.mp4"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    t0 = bounds[ids.index(sorted(want)[0])] if want else 0.0
    t1 = bounds[ids.index(sorted(want)[-1]) + 1] if want else END
    mix, sr = audio(starts, END); mix = mix[int(t0 * sr): int(t1 * sr)]
    wav = os.path.join(tmp, "a.wav"); sf.write(wav, mix, sr)
    out = os.path.join(HERE, "draft", tag + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    if not want:
        fmt = lambda s: f"{int(s)//3600:02d}:{int(s)//60%60:02d}:{int(s)%60:02d},{int(round((s % 1) * 1000)) % 1000:03d}"
        with open(out[:-4] + ".srt", "w") as fh:
            for k, (x0, x1, txt) in enumerate(caps, 1):
                fh.write(f"{k}\n{fmt(x0)} --> {fmt(x1)}\n{txt}\n\n")
    print(json.dumps({"result": "ok", "output": out, "seconds": round(t1 - t0, 2), "voice": "TEMPORARY Kokoro - not for release"}))
