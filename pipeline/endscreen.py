#!/usr/bin/env python3
"""endscreen.py - the end-screen tail of every pipeline release (owner request 2026-11-20).

YouTube end screens (the clickable "next video" / subscribe elements in the last 5-20 s) cannot be set through the
YouTube Data API v3 - there is no endpoint for them. So the pipeline does the part it can:

  * every video ends with a 20 s outro made for end-screen elements (calm background, nothing important where the
    elements sit), so the owner only has to add the elements in Studio;
  * it picks the video to recommend (a related public video of the same channel, else the newest one) and the card
    tells the owner which one, with the Studio steps.

    python3 pipeline/endscreen.py pick   --release R --status status.json         # store the recommended video on R
    python3 pipeline/endscreen.py outro  --channel oa --bg frame.png --out outro.mp4 [--seconds 20]

The outro is an ordinary video asset for the timeline's last shot; the QC gate checks that the video runs at least
15 s past the end of the narration (`endscreen tail`).
"""
import argparse, json, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E  # noqa: E402
from run import DEFAULT_STATE  # noqa: E402

TAIL_MIN_S, TAIL_MAX_S = 15.0, 20.0
STOP = {"a", "an", "the", "of", "in", "on", "to", "for", "and", "this", "that", "it", "its", "is", "was", "then", "how",
        "why", "what", "just", "from", "with", "nasa"}
STYLE = {"oa": {"accent": (255, 204, 0), "ink": (255, 255, 255), "font": "/home/user/work/fonts/anton.ttf"},
         "nx": {"accent": (70, 204, 198), "ink": (250, 241, 224), "font": "/usr/share/fonts/opentype/inter/Inter-Black.otf"}}


def _words(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 2}


def pick(videos, title, tags=(), exclude=()):
    """A related public long video of the channel (shared topic words), else the newest public long one."""
    pool = [v for v in videos if v.get("privacy") == "public" and v.get("video_id") not in exclude
            and (v.get("seconds") or 61) >= 60 and v.get("title")]
    if not pool:
        return None
    want = _words(title) | set().union(*[_words(t) for t in tags]) if tags else _words(title)
    newest = sorted(pool, key=lambda v: v.get("publishedAt") or "", reverse=True)
    scored = sorted(newest, key=lambda v: len(want & _words(v["title"])), reverse=True)
    best = scored[0] if want & _words(scored[0]["title"]) else newest[0]
    why = "related topic" if best is scored[0] and want & _words(best["title"]) else "newest public video"
    return {"video_id": best["video_id"], "title": best["title"], "why": why}


def outro(channel, bg, out, seconds=20.0, fps=30):
    """A 20 s end-screen background: the last picture of the episode, blurred and dimmed, slow push-in, a short label.
    The left 2/3 and the right third stay free for the video element and the subscribe button."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
    W, H = 1920, 1080
    st = STYLE[channel]
    base = Image.open(bg).convert("RGB").resize((W, H))
    base = ImageEnhance.Brightness(base.filter(ImageFilter.GaussianBlur(18))).enhance(0.45)
    f = ImageFont.truetype(st["font"], 64)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                          "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = int(round(seconds * fps))
    for i in range(n):
        t = i / fps
        z = 1.0 + 0.15 * t / seconds
        cw, ch = W / z, H / z
        im = base.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H))
        d = ImageDraw.Draw(im)
        for k in range(70):                                   # drifting light motes keep the tail alive (no freeze)
            sp = 20 + (k * 37) % 50
            x = (k * 271 + 13 * math.sin(t + k)) % W
            y = (k * 619 - t * sp) % H
            r = 2 + k % 3
            b = 90 + (k * 53) % 120
            d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, min(255, b + 20)))
        a = min(1.0, t / 0.6)
        col = tuple(int(c * a) for c in st["accent"])
        d.text((150, 150), "WATCH NEXT", font=f, fill=col)
        d.rectangle([150, 232, 150 + int(260 * a), 240], fill=col)
        p.stdin.write(im.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise E.PipelineError("ffmpeg failed to write the outro")
    return {"out": out, "seconds": seconds}


def studio_steps(rec):
    who = f"«{rec['title']}» (https://youtu.be/{rec['video_id']})" if rec else "последний публичный ролик канала"
    return (f"Конечная заставка: рекомендую {who}. YouTube не даёт ставить её через API, поэтому в Studio (в браузере): "
            "Контент → ролик → Конечная заставка → «Импортировать из видео» (взять заставку прошлого ролика) "
            "или шаблон «1 видео, 1 подписка» → выбрать ролик → Сохранить. Последние 20 с ролика уже свободны под неё.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default=os.environ.get("PIPELINE_STATE", DEFAULT_STATE))
    s = ap.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("pick"); x.add_argument("--release", required=True); x.add_argument("--status", required=True)
    x = s.add_parser("outro"); x.add_argument("--channel", required=True, choices=sorted(STYLE)); x.add_argument("--bg", required=True)
    x.add_argument("--out", required=True); x.add_argument("--seconds", type=float, default=20.0)
    a = ap.parse_args()
    try:
        if a.cmd == "pick":
            r = E.load(a.state, a.release)
            st = json.load(open(a.status))
            vids = st.get("videos") or st.get("channel_videos") or []
            v = E.current_version(r) or {}
            title = v.get("title") or (r.get("topic") or {}).get("title", "")
            excl = {(r.get("preview") or {}).get("video_id")}
            rec = pick(vids, title, v.get("tags") or [], excl)
            r["endscreen"] = rec
            E.log(r, "endscreen_pick", video_id=(rec or {}).get("video_id"))
            E.save(a.state, r)
            out = {"release": r["id"], "endscreen": rec, "studio": studio_steps(rec)}
        else:
            out = outro(a.channel, a.bg, a.out, a.seconds)
        print(json.dumps(out, ensure_ascii=False, indent=1))
    except (E.PipelineError, OSError, ValueError) as e:
        print(json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=1))
        sys.exit(1)


if __name__ == "__main__":
    main()
