#!/usr/bin/env python3
"""EP008 first-20-second test + cover A. Plan: packages/FIRST_20S.md. Temporary voice only (tts_temp.py, Kokoro).

    python3 hook20.py --media /home/claude/ep008-media --cover          # covers/EP008_cover_A.jpg (1280x720)
    python3 hook20.py --media /home/claude/ep008-media --render --confirm  # test/EP008_hook20_test.mp4 + .srt

Cut points come from voice_temp/timing.json (s01, s02), so picture follows the words.
Media are the NASA originals from draft release ep008-originals (fetch_manifest.tsv); nothing is upscaled
(graphics.photo asserts it). Never uploads.
"""
import argparse, json, os, subprocess, tempfile
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
import graphics as g

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1920, 1080, 30
END = 20.0                                    # set by timeline(): end of scene s03 (~38 s)
GOLD, WHITE, RED, BLACK = (255, 210, 30), (255, 255, 255), (229, 50, 45), (0, 0, 0)
LUNAR, EARTHSET, SPACER = "a2_lunar_surface_art002e009289.jpg", "a2_earthset_art002e009288.jpg", "a3_spacer_MSFC_07212026_4755.jpg"
COVER_BOX = (0.0, 0.0, 0.62, 0.523)          # same crop for the cover and frame 1 (cover promise = first frame)


def timeline():
    t = json.load(open(os.path.join(HERE, "voice_temp", "timing.json")))
    s1, s2 = t["s01"], t["s02"]
    s2_at = round(s1["dur"] + 0.35, 2)
    cut1 = round(s1["sentences"][1]["start"] - 0.07, 2)                 # "Now it won't..." -> orbit diagram
    cut2 = round(s2_at + s2["sentences"][1]["start"] - 0.1, 2)          # "And the next crew's rocket..." -> SLS
    cut3 = round(s2_at + s2["sentences"][3]["start"] - 0.05, 2)         # "a metal barrel..." -> spacer photo
    global END
    s3 = t["s03"]; s3_at = round(s2_at + s2["dur"] + 0.35, 2)
    END = round(s3_at + s3["dur"] + 0.4, 2)
    c4 = round(s3_at + s3["sentences"][1]["start"] - 0.1, 2)            # "fourteen days in orbit..." -> NASA con-ops graphic
    c5 = round(s3_at + s3["sentences"][2]["start"] - 0.1, 2)            # "Here's what they'll actually do..." -> Moon photo
    shots = [("lunar", 0.0, cut1), ("orbit", cut1, s2_at), ("earthset", s2_at, cut2), ("sls", cut2, cut3), ("spacer", cut3, s3_at),
             ("timeline", s3_at, c4), ("conops", c4, c5), ("hertz", c5, END)]
    lines = [(0.0 + x["start"], 0.0 + x["end"], x["text"]) for x in s1["sentences"]] + \
            [(s2_at + x["start"], s2_at + x["end"], x["text"]) for x in s2["sentences"]] + \
            [(s3_at + x["start"], s3_at + x["end"], x["text"]) for x in s3["sentences"]]
    return shots, lines, (s2_at, s3_at)


def badge(im, xy, text, fill, color, size=44):
    im = im.convert("RGBA"); lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = g.font(size); w = d.textlength(text, font=f); x, y = xy
    d.rounded_rectangle([x, y, x + w + 36, y + size + 24], 12, fill=fill + (235,)); d.text((x + 18, y + 6), text, font=f, fill=color)
    im.alpha_composite(lay); return im.convert("RGB")


def frame(name, u, t, media, shot_len):
    p = lambda n: os.path.join(media, n)
    if name == "lunar":
        im = g.photo(p(LUNAR), u, COVER_BOX, (0.05, 0.03, 0.60, 0.515), "NASA · ARTEMIS II PHOTO, APR 6, 2026")
        im = g.chip(im, "a2")
        a = min(1, max(0, (t - 0.2) / 0.25))
        if a > 0:
            im = g.text_on(im, (W * 0.50, H * 0.47), "ARTEMIS III PLAN:", 70, WHITE, alpha=a)
            im = g.text_on(im, (W * 0.50, H * 0.55), "LAND HERE", 120, GOLD, alpha=a)
        k = min(1, max(0, (t - (shot_len - 0.35)) / 0.25))
        if k > 0:                                                   # red strike through LAND HERE
            d = ImageDraw.Draw(im); x0, y0 = W * 0.495, H * 0.64; x1 = x0 + (W * 0.39) * k
            d.line([(x0, y0), (x1, y0 - 60 * k)], fill=RED, width=16)
        return im
    if name == "orbit":
        return g.chip(g.d_orbit_vs_moon(u), "a3plan")
    if name == "earthset":
        im = g.photo(p(EARTHSET), u, (0.08, 0.18, 0.88, 0.0), (0.13, 0.20, 0.90, 0.0), "NASA · ARTEMIS II PHOTO, APR 6, 2026")
        im = g.text_on(im, (70, 60), "ARTEMIS II · APRIL 2026", 64, GOLD, alpha=min(1, u * 6))
        im = g.text_on(im, (70, 140), "AROUND THE MOON", 52, WHITE, alpha=min(1, max(0, u * 6 - 1)))
        return g.chip(im, "a2")
    if name == "sls":
        return g.d_sls_stack(u)
    if name == "spacer":
        im = g.photo(p(SPACER), u, (0.14, 0.08, 0.86, 0.0), (0.24, 0.16, 0.76, 0.0), "NASA/SAM LOTT · MARSHALL, JULY 2026")
        im = g.text_on(im, (70, 60), "ARTEMIS III SPACER", 56, WHITE)
        im = g.text_on(im, (70, 130), "NO ENGINE", 120, GOLD, alpha=min(1, u * 4))
        return g.chip(im, "a3hw")
    if name == "timeline":
        return g.d_timeline(u)
    if name == "conops":
        b0, b1 = ((0.0, 0.0, 0.62, 0.0), (0.04, 0.05, 0.60, 0.0)) if u < 0.5 else ((0.38, 0.30, 1.0, 0.0), (0.40, 0.33, 0.98, 0.0))
        im = g.photo(p("a3_conops_oct2026.jpg"), (u % 0.5) * 2, b0, b1, "NASA CONCEPT GRAPHIC, OCT 23, 2026")
        return g.chip(im, "a3plan")
    if name == "hertz":
        im = g.photo(p("a2_hertzsprung_art002e012093.jpg"), u, (0.05, 0.10, 0.85, 0.0), (0.12, 0.16, 0.80, 0.0), "NASA · ARTEMIS II PHOTO, APR 6, 2026")
        im = g.text_on(im, (70, 60), "FIRST LANDING: ARTEMIS IV", 72, GOLD, alpha=min(1, u * 5))
        im = g.text_on(im, (70, 150), "PLANNED FOR 2028", 56, WHITE, alpha=min(1, max(0, u * 5 - 0.5)))
        return g.chip(im, "a2")


def chunks(lines, maxc=44):
    out = []
    for a, b, txt in lines:
        words = txt.split(); cur = []; parts = []
        for w_ in words:
            if cur and len(" ".join(cur + [w_])) > maxc: parts.append(" ".join(cur)); cur = []
            cur.append(w_)
        parts.append(" ".join(cur))
        if len(parts) > 1 and len(parts[-1]) < 14:                      # no orphan word at the end of a line
            parts[-2:] = [parts[-2] + " " + parts[-1]]
        n = sum(len(x) for x in parts); t = a
        for x in parts:
            d = (b - a) * len(x) / n; out.append((t, t + d, x)); t += d
    return out


def caption(im, t, caps):
    cur = [c for c in caps if c[0] <= t < c[1] + 0.12]
    if cur:
        d = ImageDraw.Draw(im)
        d.text((W // 2, H - 150), cur[-1][2], font=g.font(46, g.INTER), fill=WHITE, anchor="mm", stroke_width=5, stroke_fill=BLACK)
    return im


def sfx(sr, cut1, cut2, cut3, n):
    """Synthesised, original sound design (no library SFX): sub hit, reverse whoosh, impact, ticks, metal clank, drone."""
    a = np.zeros(n, np.float32); T = lambda s: int(s * sr)
    def add(at, sig, gain):
        i = T(at); j = min(n, i + len(sig)); a[i:j] += gain * sig[: j - i]
    tt = lambda d: np.arange(int(d * sr)) / sr
    rng = np.random.default_rng(8)
    x = tt(1.6); add(0.0, np.sin(2 * np.pi * 42 * x) * np.exp(-x * 2.6), 0.55)                       # sub hit
    x = tt(0.5); wn = rng.standard_normal(len(x)).astype(np.float32)
    wn = np.convolve(wn, np.ones(40) / 40, "same"); add(cut1 - 0.5, wn * (x / 0.5) ** 2, 0.5)         # reverse whoosh
    x = tt(0.9); add(cut1, (np.sin(2 * np.pi * 55 * x) + 0.4 * rng.standard_normal(len(x)) * np.exp(-x * 30)) * np.exp(-x * 5), 0.6)
    x = tt(0.06)
    for at in (cut1 + 1.65, cut2 + 0.2, cut2 + 4.9):
        add(at, np.sin(2 * np.pi * 1800 * x) * np.exp(-x * 80), 0.12)                                 # UI ticks
    x = tt(1.4); clank = sum(np.sin(2 * np.pi * f * x) * np.exp(-x * k) for f, k in ((310, 4), (447, 5), (691, 7), (1130, 9)))
    add(cut3 - 1.0, clank, 0.14); add(cut3, clank, 0.10)                                                # spacer seats / cut
    x = tt(END - cut1); drone = (np.sin(2 * np.pi * 55 * x) + 0.5 * np.sin(2 * np.pi * 82.5 * x)) * 0.05
    drone *= np.minimum(1, x / 1.5) * np.minimum(1, (END - cut1 - x) / 0.6); add(cut1, drone, 1.0)
    return a


def cover(media):
    src = Image.open(os.path.join(media, LUNAR)).convert("RGB"); sw, sh = src.size
    x1 = COVER_BOX[2] * sw; h = x1 * 9 / 16
    im = src.crop((0, 0, int(x1), int(h))).resize((1280, 720), Image.LANCZOS)
    # grade: lift and warm the lunar surface (golden-hour look per style guide), keep Earth blue; no content change
    im = ImageOps.autocontrast(im, cutoff=0.4, preserve_tone=True)
    r, gch, b = [np.asarray(c, np.float32) for c in im.split()]
    lum = (0.3 * r + 0.59 * gch + 0.11 * b)
    blue = np.clip((b - r) / 40, 0, 1)                         # Earth pixels
    warm = (1 - blue)
    r = r + warm * lum * 0.13; gch = gch + warm * lum * 0.05; b = b * (1 - 0.18 * warm) + blue * 30
    soft = np.asarray(Image.fromarray(np.clip(lum, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)), np.float32)
    dark = np.clip((22 - soft) / 22, 0, 1) * np.clip((40 - lum) / 40, 0, 1) * warm   # empty sky only (not crater shadows)
    r = r + dark * 4; gch = gch + dark * 14; b = b + dark * 46
    im = Image.merge("RGB", [Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)) for c in (r, gch, b)])
    im = ImageEnhance.Contrast(im).enhance(1.2); im = ImageEnhance.Color(im).enhance(1.35)
    glow = Image.new("L", im.size, 0); ImageDraw.Draw(glow).ellipse([700, 70, 1150, 420], fill=150)
    im = Image.composite(ImageEnhance.Brightness(im).enhance(1.35), im, glow.filter(ImageFilter.GaussianBlur(70)))
    # headline: two lines left, NO = gold key word
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = g.font(150); st = 9
    d.text((52, 18), "NO", font=f, fill=GOLD, stroke_width=st, stroke_fill=BLACK)
    nw = d.textlength("NO ", font=f)
    d.text((52 + nw, 18), "MOON", font=f, fill=WHITE, stroke_width=st, stroke_fill=BLACK)
    d.text((52, 190), "LANDING", font=f, fill=WHITE, stroke_width=st, stroke_fill=BLACK)
    lw = d.textlength("LANDING", font=f)
    d.line([(60, 382), (60 + lw, 382)], fill=RED, width=16)
    sh_ = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh_.paste((0, 0, 0, 200), mask=lay.split()[3])
    out = im.convert("RGBA"); out.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(7)), (8, 10)); out.alpha_composite(lay)
    out = badge(out, (52, 600), "ARTEMIS III · 2027", GOLD, BLACK, size=48)
    ImageDraw.Draw(out).text((1268, 708), "Photo: NASA, Artemis II (2026)", font=g.font(20, g.INTER), fill=WHITE, anchor="rs",
                             stroke_width=2, stroke_fill=BLACK)
    os.makedirs(os.path.join(HERE, "covers"), exist_ok=True)
    p = os.path.join(HERE, "covers", "EP008_cover_A.jpg"); out.save(p, quality=90); return p


def render(media):
    shots, lines, (s2_at, s3_at) = timeline()
    caps = chunks(lines)
    tmp = tempfile.mkdtemp(); vid = os.path.join(tmp, "v.mp4")
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    for i in range(int(END * FPS)):
        t = i / FPS
        name, a, b = next(s for s in shots if s[1] <= t < s[2])
        im = frame(name, (t - a) / (b - a), t - a, media, b - a)
        if t > END - 0.4:
            im = Image.blend(im, Image.new("RGB", (W, H)), (t - END + 0.4) / 0.4)
        pr.stdin.write(caption(im, t, caps).tobytes())
    pr.stdin.close(); pr.wait()
    v1, sr = sf.read(os.path.join(HERE, "voice_temp", "s01.wav"), dtype="float32")
    v2, _ = sf.read(os.path.join(HERE, "voice_temp", "s02.wav"), dtype="float32")
    n = int(END * sr); mix = np.zeros(n, np.float32)
    v3, _ = sf.read(os.path.join(HERE, "voice_temp", "s03.wav"), dtype="float32")
    mix[: len(v1)] += v1; i = int(s2_at * sr); mix[i: i + len(v2)] += v2[: n - i]
    i = int(s3_at * sr); mix[i: i + len(v3)] += v3[: n - i]
    mix += sfx(sr, shots[1][1], shots[3][1], shots[4][1], n)
    wav = os.path.join(tmp, "a.wav"); sf.write(wav, mix, sr)
    os.makedirs(os.path.join(HERE, "test"), exist_ok=True)
    out = os.path.join(HERE, "test", "EP008_hook30_preview.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    fmt = lambda s: f"00:{int(s)//60:02d}:{int(s)%60:02d},{int(round((s % 1) * 1000)):03d}"
    with open(out[:-4] + ".srt", "w") as fh:
        for k, (a, b, x) in enumerate(caps, 1):
            fh.write(f"{k}\n{fmt(a)} --> {fmt(b)}\n{x}\n\n")
    json.dump({"shots": shots, "voice": "TEMPORARY Kokoro am_michael", "sfx": "synthesised in hook20.py"},
              open(out[:-4] + ".timeline.json", "w"), indent=1)
    return out, shots


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--media", required=True)
    ap.add_argument("--cover", action="store_true"); ap.add_argument("--render", action="store_true"); ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()
    if a.cover:
        print(cover(a.media))
    if a.render:
        if not a.confirm:
            raise SystemExit("add --confirm")
        print(json.dumps(render(a.media)))
