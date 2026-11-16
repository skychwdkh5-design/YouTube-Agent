#!/usr/bin/env python3
"""14 s test of the kinetic captions on live NASA footage with the existing EP014 voice (no new paid audio).

  python3 -I scenes/test_captions.py --media /mnt/project-files --out caps_test.mp4 [--accent lime]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kcaps import MONO, Captions, Hero, Style  # noqa: E402

W, H, FPS, DUR = 1920, 1080, 30, 14.0
N = int(DUR * FPS)
# (shot start, shot end, file under media_v2/cuts, source in-point, push-in %)
SHOTS = [(0.0, 3.5, "a_darkmoon2.mp4", 1.10, 5), (3.5, 7.5, "a_window1.mp4", 0.0, 4),
         (7.5, 9.9, "a_window2.mp4", 0.0, 3), (9.9, 14.0, "a_crewview.mp4", 20.0, 7)]
VOICE_END = 13.30


def frames(media, tmp):
    out = []
    for i, (a, b, f, ss, _) in enumerate(SHOTS):
        n = int(round((b - a) * FPS))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-i", str(media / "media_v2/cuts" / f),
                        "-frames:v", str(n), "-vf", "scale=1920:1080", "-q:v", "2", str(tmp / f"s{i}_%04d.jpg")], check=True)
        out.append(sorted(tmp.glob(f"s{i}_*.jpg")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--accent", default="yellow", choices=["yellow", "lime"])
    ap.add_argument("--frames", help="comma list of times -> PNG stills only")
    a = ap.parse_args()
    vj = json.loads((a.media / "artemis/EP014/voice/narration.voice.json").read_text())
    words = [w for w in vj["words"] if w["end"] <= VOICE_END + 0.01]
    st = Style(accent=(255, 210, 31) if a.accent == "yellow" else (198, 255, 0))
    ws = {w["text"]: w for w in words}
    hero = Hero(ws["forty-six"]["start"] - 0.05, DUR, "46,000", above="ORION WAS", below="MILES AWAY")
    caps = Captions(words, keywords={"FIVE", "PINPRICKS", "DARK", "MOON.", "MOON", "THREE", "ASTRONAUTS", "ARTEMIS", "II"},
                    heroes=[hero], replace={"Two": "II"}, style=st, duration=DUR)
    mf = ImageFont.truetype(MONO, 20)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fr = frames(a.media, tmp)
        times = [float(x) for x in a.frames.split(",")] if a.frames else [i / FPS for i in range(N)]
        proc = None
        if not a.frames:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(a.media / "artemis/EP014/voice/narration.wav"),
                            "-t", f"{DUR}", "-af", f"afade=t=out:st={VOICE_END + 0.2}:d=0.4", str(tmp / "v.wav")], check=True)
            proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                     "-r", str(FPS), "-i", "-", "-i", str(tmp / "v.wav"), "-c:v", "libx264", "-preset", "medium",
                                     "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                                     "-shortest", str(a.out)], stdin=subprocess.PIPE)
        for t in times:
            k = next(i for i, s in enumerate(SHOTS) if s[0] <= t < s[1] or i == len(SHOTS) - 1)
            s0, s1, _, _, push = SHOTS[k]
            idx = min(len(fr[k]) - 1, int((t - s0) * FPS))
            im = Image.open(fr[k][idx]).convert("RGBA")
            z = 1 + push / 100 * (t - s0) / (s1 - s0)
            inv = 1 / z
            im = im.transform((W, H), Image.Transform.AFFINE, (inv, 0, W / 2 * (1 - inv), 0, inv, H / 2 * (1 - inv)),
                              resample=Image.Resampling.BICUBIC)
            d = ImageDraw.Draw(im)
            d.text((84, H - 96), "ARCHIVE  //  NASA ARTEMIS II", font=mf, fill=(255, 255, 255, 190))
            caps.render(im, t)
            if a.frames:
                im.convert("RGB").save(a.out.parent / f"cap_{t:05.2f}.png")
            else:
                proc.stdin.write(im.convert("RGB").tobytes())
        if proc:
            proc.stdin.close()
            if proc.wait():
                raise SystemExit("ffmpeg failed")
    print("done")


if __name__ == "__main__":
    main()
