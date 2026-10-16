"""S3 V3 post: grade the path-traced HDR frames, draw the 2-D layer (kinetic type, labels anchored to 3-D points through the same camera,
pore-water glows depth-tested against the rendered distance, chips), dissolve into EVIDENCE MAP PENDING, add the CC0 sound, encode for iPad.
    python3 compose_v3.py TAG OUT.mp4 [--from A --to B]    (frames from WORK/TAG/hdr_NNNN.npy)"""
import os, sys, json, wave, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orbitalatlas import pbrt3d as P, easing as E, typeset as TS, kinetic as K, textrec as TR, illustrate as I, sfx
import scene_v3 as V
import run_v3 as R

W, H, FPS = 1920, 1080, 30
AMBER8, CYAN8, WHITE8 = (255, 194, 71), (92, 225, 230), (240, 244, 248)
CAPTIONS = [(0.5, 2.4, "A radar satellite pings the same patch of ground", ("same",)),
            (2.4, 4.0, "and records exactly how far away it is.", ("far",)),
            (4.3, 5.8, "Pump out groundwater and the pressure drops,", ("pressure",)),
            (5.8, 7.4, "the clay squeezes, and the ground sinks.", ("sinks.",)),
            (7.6, 9.6, "On the next pass, the echo travels farther.", ("farther.",))]
LABELS = [(4.5, 5.75, "WATER PRESSURE DROPS", "well"), (5.95, 7.2, "CLAY COMPACTS", "clay"), (8.75, 9.6, "EXTRA PATH", "extra")]
CUES = [dict(t=0.20, kind="whoosh", why="satellite arrives"), dict(t=1.65, kind="sweep", why="pulse 1"), dict(t=2.30, kind="tick", why="echo 1 returns"),
        dict(t=3.40, kind="whoosh", why="street skim"), dict(t=3.90, kind="whoosh", why="whip down under the surface"), dict(t=4.20, kind="rise", why="pumping starts"),
        dict(t=4.50, kind="ui_blip", why="label"), dict(t=5.95, kind="ui_blip", why="label"), dict(t=7.25, kind="whoosh", why="whip up to the satellite"),
        dict(t=7.50, kind="sweep", why="pulse 2"), dict(t=8.10, kind="tick", why="echo 2 returns"), dict(t=8.75, kind="ui_blip", why="extra path"),
        dict(t=9.95, kind="impact", why="LINE OF SIGHT lockup"), dict(t=11.9, kind="whoosh", why="camera to the top view")]
END3D, CARD0 = 12.75, 12.45                       # last 3-D frame time; the placeholder dissolves in from CARD0


def project(p, cam):
    e, g, f, sh = cam; x, y, z = P.project(p, e, g, f, (W, H)); return x, y + sh, z


def anchor(which, t):
    if which == "well":
        b = V.boundaries(V.WELL_X, 0.0, t); return (V.WELL_X, -0.3, max(float(b[2] + 0.5 * (b[3] - b[2])), V.head(t)))
    if which == "clay":
        b = V.boundaries(9.0, 0.0, t); return (9.0, -0.1, float(b[3] + 0.5 * (b[4] - b[3])))
    R0 = float(np.linalg.norm(V.P0 - V.SAT)); u2 = (V.PEND - V.SAT) / np.linalg.norm(V.PEND - V.SAT); Q = V.SAT + u2 * R0; return tuple((Q + V.PEND) / 2)


def drops(img, t, cam, dist, scene):
    pts = scene.porewater(t)
    if not pts: return img
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(glow); sx, sy = dist.shape[1] / W, dist.shape[0] / H
    for p, a in pts:
        x, y, z = project(p, cam)
        if z <= 0 or not (0 <= x < W and 0 <= y < H): continue
        dd = float(dist[int(y * sy), int(x * sx)])
        if 0 < dd < z - 0.6: continue                                          # hidden behind rendered geometry
        r = max(1.5, 0.12 * 1150 / z)
        d.ellipse([x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2], fill=(80, 190, 255, int(45 * a)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 240, 255, int(235 * a)))
    glow = glow.filter(ImageFilter.GaussianBlur(1.2)); out = img.convert("RGBA"); out.alpha_composite(glow); return out.convert("RGB")


def captions(ui, t):
    for t0, t1, s, emph in CAPTIONS:
        if not (t0 <= t <= t1): continue
        a = E.smooth(E.seg(t, t0, t0 + 0.25)) * (1 - E.smooth(E.seg(t, t1 - 0.2, t1)))
        if a > 0.01:
            bd = np.clip((np.arange(300) - 40) / 260.0, 0, 1) ** 1.2 * 170 * a; band = Image.fromarray(bd.astype(np.uint8)[:, None]).resize((W, 300))
            sh = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); sh.putalpha(band); ui.alpha_composite(sh, (0, H - 300))
        px = 52; words = s.split(" "); pos, _ = TS.layout(words, px, "bold", 1700, align="center", x0=W / 2, y0=905)
        prev = TR.STATE["tag"]; TR.STATE["tag"] = "WordCaptions"
        try:
            for i, w_ in enumerate(words):
                TS.animate_word(ui, w_, pos[i][0], pos[i][1], px, t, t0 + i * 0.045, preset="rise", weight="bold", color=WHITE8, emph=w_ in emph, accent=AMBER8,
                                dur=0.3, exit_t=t1 - 0.22, exit="up", hold_glint=False)
        finally: TR.STATE["tag"] = prev


def labels(ui, t, cam):
    d = ImageDraw.Draw(ui, "RGBA")
    for t0, t1, s, which in LABELS:
        if not (t0 <= t <= t1): continue
        a = E.out_cubic(E.seg(t, t0, t0 + 0.3)) * (1 - E.smooth(E.seg(t, t1 - 0.25, t1))); x, y, z = project(anchor(which, t), cam)
        if z <= 0 or a < 0.02: continue
        p = (x, y); px = 36; w_ = K.width(s, px, "black"); lx = min(max(p[0] + 70, 80), W - 80 - w_); ly = min(max(p[1] - 120, 200), 800)
        q = (lx - 10, ly + px * 0.62); e = E.out_cubic(E.seg(t, t0, t0 + 0.35))
        d.line([p, (p[0] + (q[0] - p[0]) * e, p[1] + (q[1] - p[1]) * e)], fill=(255, 255, 255, int(220 * a)), width=3)
        d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], outline=(255, 255, 255, int(230 * a)), width=3)
        pad = px * 0.35; d.rounded_rectangle([lx - pad, ly - pad * 0.6, lx + w_ + pad, ly + px * 1.3], radius=px * 0.2, fill=(6, 10, 16, int(170 * a)))
        TS.animate_word(ui, s, lx, ly, px, t, t0, preset="slide", weight="black", color=WHITE8, dur=0.35)


def lockup(ui, t):
    t0, t1 = 9.95, 11.75
    if not (t0 <= t <= t1): return
    x, y, xx = 960, 640, 960                                                  # over the dark strata, clear of the beam
    for i, w_ in enumerate(["LINE", "OF", "SIGHT"]):
        TS.animate_word(ui, w_, xx, y, 100, t, t0 + i * 0.09, preset="depth_in", weight="black", color=CYAN8, dur=0.45, exit_t=t1 - 0.3, exit="up"); xx += K.width(w_, 100, "black") + 32
    TS.animate_word(ui, "NOT THE VERTICAL DROP", x + 6, y + 140, 50, t, t0 + 0.55, preset="outline_fill", weight="black", color=WHITE8, dur=0.5, exit_t=t1 - 0.3, exit="up")


def chips(ui, t):
    d = ImageDraw.Draw(ui, "RGBA"); a_all = 1 - E.smooth(E.seg(t, CARD0, CARD0 + 0.3))
    items = [("SCIENTIFIC ILLUSTRATION · NOT A REAL SITE · NOT TO SCALE", 0.0)] + ([("DROP EXAGGERATED", V.TL["sink"][0])] if t >= V.TL["sink"][0] else [])
    for i, (s, t0) in enumerate(items):
        a = E.out_cubic(E.seg(t, t0, t0 + 0.4)) * a_all
        if a < 0.02: continue
        px = 30; f = K.face(px, "bold"); w_ = f.getlength(s); x, y = 72, 50 + i * 54
        d.rounded_rectangle([x, y, x + w_ + px * 1.2, y + px * 1.45], radius=px * 0.25, fill=(0, 0, 0, int(150 * a)))
        d.rectangle([x, y, x + px * 0.18, y + px * 1.45], fill=AMBER8 + (int(255 * a),))
        d.text((x + px * 0.6, y + px * 0.18), s, font=f, fill=(235, 240, 246, int(255 * a))); TR.note(s, px, (x, y, x + w_ + px * 1.2, y + px * 1.45), (235, 240, 246), a)


def frame(i, tag, scene, card):
    t = i / FPS; work = os.path.join(R.WORK, tag)
    if t >= CARD0 + 0.6: return card.render(t - CARD0)
    j = min(i, int(round(END3D * FPS)) - 1)
    while j > 0 and not os.path.exists(os.path.join(work, f"frame_{j:04d}.npz")) and not os.path.exists(os.path.join(work, f"hdr_{j:04d}.npy")): j -= 1   # PREVIEW renders every 2nd frame
    z = os.path.join(work, f"frame_{j:04d}.npz")
    if os.path.exists(z): f_ = np.load(z); hdr, dist = f_["hdr"].astype(np.float32), f_["dist"].astype(np.float32)
    else: hdr = np.load(os.path.join(work, f"hdr_{j:04d}.npy")).astype(np.float32); dist = np.load(os.path.join(work, f"dist_{j:04d}.npy")).astype(np.float32)
    img = Image.fromarray(R.grade(hdr, dist))
    if img.size != (W, H): img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
    cam = V.cam(t); img = drops(img, t, cam, dist, scene)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); captions(ui, t); labels(ui, t, cam); lockup(ui, t); chips(ui, t)
    out = img.convert("RGBA"); out.alpha_composite(ui); out = out.convert("RGB")
    if t >= CARD0: out = Image.blend(out, card.render(t - CARD0), E.smooth(E.seg(t, CARD0, CARD0 + 0.6)))
    return out


def audio(path, dur):
    silent = path + ".silent.wav"
    with wave.open(silent, "wb") as w_: w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(sfx.SR); w_.writeframes(np.zeros((int(dur * sfx.SR), 2), np.int16).tobytes())
    raw = path + ".raw.wav"; rep = sfx.mix(silent, CUES, dur, raw, normalise=False); os.remove(silent)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "volume=8dB,alimiter=limit=0.70", path], check=True); os.remove(raw); return rep


def encode(tag, out, a=0, b=None, dur=V.DUR):
    scene = V.SceneV3(R.WORK, R.TEX); card = I.EvidencePending((W, H), 2.0); b = b or int(round(dur * FPS))
    wav = out + ".wav"; rep = audio(wav, dur); json.dump(rep, open(out + ".sfx.json", "w"), indent=1)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", f"{a / FPS:.4f}", "-i", wav, "-af", "apad", "-shortest", "-c:a", "aac", "-b:a", "192k",
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(a, b): p.stdin.write(np.asarray(frame(i, tag, scene, card), np.uint8).tobytes())
    p.stdin.close(); assert p.wait() == 0; return b - a


if __name__ == "__main__":
    tag, out = sys.argv[1], sys.argv[2]
    a = int(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 0; b = int(sys.argv[sys.argv.index("--to") + 1]) if "--to" in sys.argv else None
    print("frames", encode(tag, out, a, b))
