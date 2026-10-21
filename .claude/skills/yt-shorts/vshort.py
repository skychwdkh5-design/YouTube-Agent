#!/usr/bin/env python3
"""vshort.py - a vertical 1080x1920 Short cut from a FINISHED episode video, with its approved narration, word-lit captions and kinetic type.

    python3 vshort.py spec.json                    # plan only: validates, prints what would be made
    python3 vshort.py spec.json --out short.mp4 --confirm

Free and local (ffmpeg + libass). No new voice is ever generated: the audio is the episode's own track between t0 and t1, and every caption word
comes from the episode's word timings (nothing is typed in). spec.json:
  source {video, voice_json}, t0, t1, crop [x, y, w, h] of the source frame that carries the picture, hook {text, accent}, kicks [{at, text}], chip,
  endcard {title, line}, loop (bool, hold the last card)
Layout (Shorts safe zone): text inside x 80-1000, y 250-1500; the picture is a band in the middle, never under the platform buttons.
"""
import json, os, re, subprocess, sys

W, H, FPS = 1080, 1920, 30
BG = "0A1020"
AMBER, WHITE, CYAN = "FFD23F", "FFFFFF", "6AD7E5"


def bgr(hex6):
    return hex6[4:6] + hex6[2:4] + hex6[0:2]          # ASS colours are BGR


def words_in(voice_json, t0, t1):
    ws = json.load(open(voice_json, encoding="utf-8"))["words"]
    out = [w for w in ws if w["start"] >= t0 - 0.02 and w["end"] <= t1 + 0.05]
    if not out:
        raise SystemExit("no narration words between t0 and t1")
    return out


def validate(spec):
    for k in ("source", "t0", "t1", "crop", "hook"):
        if k not in spec:
            raise SystemExit(f"spec needs '{k}'")
    d = spec["t1"] - spec["t0"] + (spec.get("endcard") and spec["endcard"].get("seconds", 2.0) or 0)
    if not 8 <= d <= 60:
        raise SystemExit(f"a Short of {d:.1f}s is outside 8-60 s")
    for f in (spec["source"]["video"], spec["source"]["voice_json"]):
        if not os.path.exists(f):
            raise SystemExit(f"missing {f}")
    return d


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ass(spec, words):
    t0, dur = spec["t0"], spec["t1"] - spec["t0"]
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Hook,Inter,112,&H00{bgr(WHITE)},&H00{bgr(WHITE)},&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,2,8,80,80,300,1
Style: Kick,Inter,76,&H00{bgr(AMBER)},&H00{bgr(AMBER)},&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,8,80,80,330,1
Style: Cap,Inter,74,&H00{bgr(WHITE)},&H00{bgr(WHITE)},&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,90,90,500,1
Style: Chip,Inter,34,&H00{bgr(WHITE)},&H00{bgr(WHITE)},&H00000000,&H78000000,-1,0,0,0,100,100,1,0,3,3,0,7,60,60,240,1
Style: End,Inter,92,&H00{bgr(WHITE)},&H00{bgr(WHITE)},&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,2,5,80,80,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    ev = []
    hook = spec["hook"]
    ht = hook["text"].upper()
    acc = hook.get("accent")
    if acc:
        ht = ht.replace(acc.upper(), "{\\c&H" + bgr(AMBER) + "&}" + acc.upper() + "{\\c&H" + bgr(WHITE) + "&}")
    # hook pops in on frame 0 (scale 140 -> 100 with a fade) and leaves after hook.seconds
    hs = hook.get("seconds", 3.0)
    fs_h = max(56, min(112, int(920 / max(len(l) for l in hook["text"].split("\n")) * 1.85)))     # longest line must fit the safe width
    ev.append(f"Dialogue: 2,{ts(0)},{ts(hs)},Hook,,0,0,0,,{{\\fs{fs_h}\\fad(0,250)\\fscx140\\fscy140\\t(0,260,\\fscx100\\fscy100)}}{ht.replace(chr(10), chr(92) + 'N')}")
    for k in spec.get("kicks", []):
        fs = max(44, min(76, int(900 / max(len(k["text"]), 1) * 1.75)))        # fit one line inside the safe width (x 80-1000)
        ev.append(f"Dialogue: 2,{ts(k['at'])},{ts(k['at'] + k.get('seconds', 2.6))},Kick,,0,0,0,,{{\\fs{fs}\\fad(120,200)\\move(540,560,540,520,0,200)}}{k['text'].upper()}")
    if spec.get("chip"):
        ev.append(f"Dialogue: 1,{ts(0)},{ts(dur)},Chip,,0,0,0,,{spec['chip'].upper()}")
    # captions: 4 words per line, the spoken word lit amber
    lines, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == 4 or w["text"].endswith((".", "?", "!")):
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    for ln in lines:
        for i, w in enumerate(ln):
            a = w["start"] - t0
            b = (ln[i + 1]["start"] - t0) if i + 1 < len(ln) else (w["end"] - t0 + 0.25)
            txt = " ".join(("{\\c&H" + bgr(AMBER) + "&}" + x["text"].upper() + "{\\c&H" + bgr(WHITE) + "&}") if j == i else x["text"].upper() for j, x in enumerate(ln))
            ev.append(f"Dialogue: 3,{ts(a)},{ts(b)},Cap,,0,0,0,,{txt}")
    ec = spec.get("endcard")
    if ec:
        s = dur
        e = dur + ec.get("seconds", 2.0)
        ev.append(f"Dialogue: 4,{ts(s)},{ts(e)},End,,0,0,0,,{{\\fad(200,0)}}{ec['title'].upper().replace(chr(10), chr(92) + 'N')}\\N{{\\fs50\\c&H{bgr(CYAN)}&}}{ec['line'].upper()}")
    return head + "\n".join(ev) + "\n"


def build(spec, out):
    words = words_in(spec["source"]["voice_json"], spec["t0"], spec["t1"])
    total = validate(spec)
    dur = spec["t1"] - spec["t0"]
    work = out + ".work"
    os.makedirs(work, exist_ok=True)
    assp = os.path.join(work, "short.ass")
    open(assp, "w", encoding="utf-8").write(ass(spec, words))
    x, y, w, h = spec["crop"]
    ph = int(round(1080 * h / w / 2) * 2)               # picture band height at 1080 wide
    py = spec.get("band_y", 700)
    nfr = int(total * FPS)
    # slow push-in on the picture (no static band): zoompan on the cropped region, 1.0 -> 1.10 over the clip
    vf = (f"[0:v]trim={spec['t0']}:{spec['t1']},setpts=PTS-STARTPTS,fps={FPS},split=2[s1][s2];"
          f"[s1]crop={w}:{h}:{x}:{y},scale={W*2}:-2:flags=lanczos,"
          f"zoompan=z='1+0.05*on/{int(dur*FPS)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{ph}:fps={FPS},format=yuv420p[pic];"
          f"[s2]scale=-2:{H}:flags=bilinear,crop={W}:{H},boxblur=36:3,eq=brightness=-0.04:saturation=0.9:contrast=1.1,format=yuv420p[bg];"   # the same footage, enlarged and blurred, fills the tall frame: no dead black
          f"[bg][pic]overlay=0:{py}:eof_action=pass,"
          f"drawbox=x=0:y={py}:w={W}:h=3:color=0x{AMBER}@0.9:t=fill,drawbox=x=0:y={py+ph-3}:w={W}:h=3:color=0x{AMBER}@0.9:t=fill,"
          f"ass={assp}:fontsdir=/usr/share/fonts/opentype/inter[v]")
    af = f"[0:a]atrim={spec['t0']}:{spec['t1']},asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-1.5:LRA=7,apad=whole_dur={total},afade=t=out:st={total-0.4}:d=0.4[a]"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", spec["source"]["video"], "-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]", "-t", f"{total}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
           "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("ffmpeg failed: " + r.stderr[-500:])
    return {"status": "ok", "out": out, "seconds": total, "words": len(words), "frames": nfr}


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(sys.argv[1]))
    for k in ("video", "voice_json"):
        p = spec["source"][k]
        spec["source"][k] = p if os.path.isabs(p) else os.path.join(base, p)
    total = validate(spec)
    if "--confirm" not in sys.argv:
        print(json.dumps({"status": "confirm_required", "seconds": total, "words": len(words_in(spec["source"]["voice_json"], spec["t0"], spec["t1"]))}))
        return 0
    out = sys.argv[sys.argv.index("--out") + 1]
    print(json.dumps(build(spec, out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
