#!/usr/bin/env python3
"""before_after.py - one light 720p comparison video of changed stretches: for each stretch a title card, then the OLD render (BEFORE) and the NEW preview (AFTER)
of the same seconds with the same narration, each with a corner badge. Only re-encodes short clips; never renders a film.

    python3 before_after.py --before render/final.mp4 --out render/EP005_before_after_720p.mp4 --seconds 30 \
        --scene "Plan: what was reported" 52.04 render/pv2_plan/pv2_plan.mp4 49.242 [--scene ...]

--scene NAME START_S PREVIEW_MP4 PREVIEW_FROM_S: START_S is the second in the OLD video where the stretch begins; PREVIEW_FROM_S is the second of the full film at which the
preview file begins (the `from` printed by `orchestrate.py render-test --start`). The AFTER clip is cut at START_S - PREVIEW_FROM_S inside the preview.
"""
import argparse, os, subprocess, sys, tempfile

FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
VF = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p"
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "29", "-r", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-ar", "44100", "-ac", "2"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg failed: {r.stderr[-600:]}")


def esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def clip(src, ss, secs, badge, out, color):
    vf = VF + f",drawtext=fontfile={FONT}:text='{badge}':fontcolor=white:fontsize=30:box=1:boxcolor={color}@0.85:boxborderw=12:x=24:y=64"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.3f}", "-t", f"{secs:.3f}", "-i", src, "-vf", vf] + ENC + [out])


def card(text, sub, out, secs=2.5):
    vf = (f"drawtext=fontfile={FONT}:text='{esc(text)}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2-30,"
          f"drawtext=fontfile={FONT}:text='{esc(sub)}':fontcolor=0xb0b8c4:fontsize=30:x=(w-text_w)/2:y=(h-text_h)/2+40")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x0b1220:s=1280x720:r=30:d={secs}", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
         "-t", str(secs), "-vf", vf + ",format=yuv420p"] + ENC + [out])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--before", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--scene", nargs=4, action="append", metavar=("NAME", "START_S", "PREVIEW_MP4", "PREVIEW_FROM_S"), required=True)
    a = ap.parse_args(argv)
    tmp = tempfile.mkdtemp()
    parts = []
    for i, (name, start, prev, pfrom) in enumerate(a.scene):
        start, pfrom = float(start), float(pfrom)
        c = os.path.join(tmp, f"{i}c.mp4"); b = os.path.join(tmp, f"{i}b.mp4"); f = os.path.join(tmp, f"{i}a.mp4")
        card(name, f"from {int(start // 60)}:{int(start % 60):02d} in the film, {a.seconds:g} s each", c)
        clip(a.before, start, a.seconds, "BEFORE", b, "0xb3261e")
        clip(prev, start - pfrom, a.seconds, "AFTER", f, "0x1a7f37")
        parts += [c, b, f]
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", a.out])
    print(os.path.getsize(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
