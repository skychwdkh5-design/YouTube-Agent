#!/usr/bin/env python3
"""Artemis III - first-20-second test (runs to the end of the hook sentence, ~24 s): NASA stills + original graphics + TEMPORARY local voice.

    python3 build_hook20.py --board                     # storyboard PNG now; empty NASA slots are labelled
    python3 build_hook20.py --render --confirm           # 20 s test MP4 - refuses until the NASA originals exist

Picture: assets/n1-boosters.jpg and assets/n4-conops.jpg (NASA, ASSETS_NEEDED.md) + NEXORA line-art cards.
Voice: voice_temp/l000..l005.wav from voice_temp.py (Kokoro, local, free) - NOT for release.
Timing comes from ../edit_plan_shots.csv and ../voice_temp/lines.json (preprod.py), so the test cuts exactly
where the full edit cuts. Prints JSON. Never uploads.
"""
import csv, json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
W, H, FPS = 1920, 1080, 30
HOOK_LAST_SCENE = "h3-conops"   # test ends after the hook's open loop closes (~24 s), never mid-sentence
INK, DIM, ACC, BG = (240, 244, 250), (150, 162, 180), (255, 196, 64), (8, 14, 26)
FONT = next((p for p in ("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
                         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if os.path.exists(p)), None)
f = lambda s: ImageFont.truetype(FONT, s) if FONT else ImageFont.load_default()


def _end():
    L = json.load(open(os.path.join(ROOT, "voice_temp", "lines.json")))
    t, prev, end = 0.0, None, 20.0
    for l in L:
        if prev is not None:
            t += 0.80 if l["scene"] != prev else 0.30
        if l["scene"] == HOOK_LAST_SCENE:
            end = t + l["dur"] + 0.6
        t += l["dur"]; prev = l["scene"]
    return round(end, 2)


END = _end()


def shots():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "edit_plan_shots.csv"))))
    return [r for r in rows if float(r["in_s"]) < END]


def voice_lines():
    L = json.load(open(os.path.join(ROOT, "voice_temp", "lines.json")))
    t, out, prev = 0.0, [], None
    # same spacing rules as preprod.py (0.30 s between lines, 0.80 s at a scene change, no chapter in the hook)
    for l in L:
        if prev is not None:
            t += 0.80 if l["scene"] != prev else 0.30
        if t >= END: break
        out.append({**l, "start": round(t, 2)}); t += l["dur"]; prev = l["scene"]
    return out


def slot_frame(name, credit):
    im = Image.new("RGB", (W, H), (34, 38, 46)); d = ImageDraw.Draw(im)
    for x in range(-H, W, 60): d.line([(x, 0), (x + H, H)], fill=(44, 48, 58), width=14)
    d.rectangle([40, 40, W - 40, H - 40], outline=ACC, width=6)
    d.text((W // 2, H // 2 - 40), f"EMPTY SLOT: {name}", font=f(64), fill=ACC, anchor="mm")
    d.text((W // 2, H // 2 + 40), f"NASA original pending - {credit} - see ASSETS_NEEDED.md", font=f(34), fill=INK, anchor="mm")
    return im


def photo_frame(path, u, credit, rect0=(0.5, 0.70, 1.0), rect1=(0.5, 0.40, 1.10)):
    src = Image.open(path).convert("RGB")
    cx = rect0[0] + (rect1[0] - rect0[0]) * u; cy = rect0[1] + (rect1[1] - rect0[1]) * u; z = rect0[2] + (rect1[2] - rect0[2]) * u
    sw, sh = src.size; ar = W / H
    cw = min(sw, sh * ar) / z; ch = cw / ar
    x0 = min(max(cx * sw - cw / 2, 0), sw - cw); y0 = min(max(cy * sh - ch / 2, 0), sh - ch)
    im = src.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)
    ImageDraw.Draw(im).text((W - 36, H - 30), credit, font=f(26), fill=INK, anchor="rs", stroke_width=2, stroke_fill=(0, 0, 0))
    return im


def card_frame(asset, text, u):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    cx, cy, r = W * 0.72, H * 0.52, 300
    if asset == "g-moon-x":                     # Moon outline + strike (own line art)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=DIM, width=8)
        k = min(1, u * 2.2); d.line([(cx - r * 0.8, cy + r * 0.8), (cx - r * 0.8 + 1.6 * r * k, cy + r * 0.8 - 1.6 * r * k)], fill=ACC, width=18)
    elif asset == "g-feb-orbit":                # Earth outline + orbit ring drawing
        d.ellipse([cx - 220, cy - 220, cx + 220, cy + 220], outline=(90, 150, 230), width=8)
        ang = 360 * min(1, u * 1.3); d.arc([cx - 320, cy - 320, cx + 320, cy + 320], -90, -90 + ang, fill=ACC, width=8)
    d.text((110, H * 0.42), text.replace(" · ", "\n"), font=f(76), fill=INK, spacing=18)
    d.text((110, H - 70), "NEXORA GRAPHIC - ILLUSTRATION", font=f(24), fill=DIM)
    return im


def frame_at(t, plan, have, board=False):
    s = next(x for x in plan if float(x["in_s"]) <= t < float(x["out_s"]))
    u = (t - float(s["in_s"])) / max(float(s["out_s"]) - float(s["in_s"]), 0.01)
    if s["kind"] == "photo":
        p = os.path.join(ROOT, "assets", s["asset_or_graphic"] + ".jpg")
        im = photo_frame(p, u, s["credit_on_screen"]) if p in have else slot_frame(s["asset_or_graphic"], s["credit_on_screen"])
        if s["on_screen_text"]:
            ImageDraw.Draw(im).text((90, 90), s["on_screen_text"], font=f(52), fill=ACC, stroke_width=3, stroke_fill=(0, 0, 0))
        if "conops" in s["asset_or_graphic"]:
            ImageDraw.Draw(im).text((90, H - 60), "NASA CONCEPT GRAPHIC", font=f(28), fill=INK, stroke_width=2, stroke_fill=(0, 0, 0))
    else:
        im = card_frame(s["asset_or_graphic"], s["on_screen_text"], u)
    return im, s


def captions(img, t, lines):
    cur = [l for l in lines if l["start"] <= t < l["start"] + l["dur"]]
    if cur:
        d = ImageDraw.Draw(img); d.text((W // 2, H - 150), cur[0]["text"], font=f(44), fill=INK, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    return img


def main(a):
    plan, lines = shots(), voice_lines()
    need = sorted({os.path.join(ROOT, "assets", s["asset_or_graphic"] + ".jpg") for s in plan if s["kind"] == "photo"})
    have = {p for p in need if os.path.exists(p)}
    if "--board" in a:
        times = [0.3, 1.8, 3.2, 4.5, 8.0, 12.0, 14.0, 18.5]
        tiles = []
        for t in times:
            im, s = frame_at(t, plan, have); im = captions(im, t, lines).resize((640, 360))
            ImageDraw.Draw(im).text((10, 8), f"{t:4.1f}s {s['scene']}", font=f(22), fill=ACC, stroke_width=2, stroke_fill=(0, 0, 0))
            tiles.append(im)
        board = Image.new("RGB", (640 * 4, 360 * 2), (0, 0, 0))
        for i, im in enumerate(tiles): board.paste(im, ((i % 4) * 640, (i // 4) * 360))
        out = os.path.join(HERE, "hook20_board.png"); board.save(out)
        print(json.dumps({"result": "ok", "board": out, "missing_slots": [os.path.basename(p) for p in need if p not in have]})); return 0
    if "--render" in a:
        missing = [os.path.basename(p) for p in need if p not in have]
        if missing:
            print(json.dumps({"result": "REFUSED", "reason": "NASA originals missing - no test with placeholders", "missing": missing})); return 2
        if "--confirm" not in a:
            print(json.dumps({"result": "REFUSED", "reason": "add --confirm"})); return 2
        for l in lines:
            if not os.path.exists(os.path.join(ROOT, l["file"])):
                print(json.dumps({"result": "REFUSED", "reason": "temp voice missing - run voice_temp.py", "file": l["file"]})); return 2
        tmp = tempfile.mkdtemp()
        vid = os.path.join(tmp, "v.mp4")
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
        for i in range(int(END * FPS)):
            t = i / FPS; im, _ = frame_at(t, plan, have)
            if t > END - 0.5: im = Image.blend(im, Image.new("RGB", (W, H)), (t - END + 0.5) / 0.5)
            p.stdin.write(captions(im, t, lines).tobytes())
        p.stdin.close(); p.wait()
        ins, fl = [], []
        for k, l in enumerate(lines):
            ins += ["-i", os.path.join(ROOT, l["file"])]; ms = int(l["start"] * 1000)
            fl.append(f"[{k + 1}:a]aresample=48000,adelay={ms}|{ms},apad[a{k}]")
        mix = ";".join(fl) + ";" + "".join(f"[a{k}]" for k in range(len(lines))) + f"amix=inputs={len(lines)}:normalize=0,atrim=0:{END},loudnorm=I=-16:TP=-1.5[a]"
        out = os.path.join(HERE, "artemis3-hook20-test.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, *ins, "-filter_complex", mix, "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", out], check=True)
        print(json.dumps({"result": "ok", "output": out, "voice": "TEMPORARY local Kokoro - not for release"})); return 0
    print(__doc__); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
