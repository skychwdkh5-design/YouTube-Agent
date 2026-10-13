"""Audio-visual helpers: transcript search on provider word timings, sentence-based subtitle cues, ASS output, audio mastering.
Nothing here estimates timing: every time comes from the provider's word-level alignment."""
import re, subprocess, json
import numpy as np

def _norm(s): return re.sub(r"[^\w\-]", "", s.lower())

class Transcript:
    def __init__(self, words, offset=0.0): self.w = words; self.off = offset
    def find(self, seq, occ=1):
        toks = [_norm(x) for x in seq.split()]; n = len(toks); hit = 0
        for i in range(len(self.w)-n+1):
            if [_norm(w["text"]) for w in self.w[i:i+n]] == toks:
                hit += 1
                if hit == occ: return i
        raise KeyError(f"{seq!r} #{occ}")
    def start(self, seq, occ=1): return self.off + self.w[self.find(seq, occ)]["start"]
    def end(self, seq, occ=1): n = len(seq.split()); return self.off + self.w[self.find(seq, occ)+n-1]["end"]

def build_cues(words, max_line=42, min_dur=0.9, lead=0.05, hold=0.3, gap=0.04):
    """one cue per sentence (long sentences split at a comma), two balanced lines, exact words, no overlaps."""
    sents, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?][\"')]*$", w["text"]): sents.append(cur); cur = []
    if cur: sents.append(cur)
    groups = []
    for s in sents:
        text = " ".join(w["text"] for w in s)
        if len(text) <= 2*max_line - 4: groups.append(s); continue
        commas = [i for i, w in enumerate(s[:-1]) if w["text"].endswith((",", ";", ":"))]
        k = min(commas, key=lambda i: abs(len(" ".join(x["text"] for x in s[:i+1])) - len(text)/2)) if commas else len(s)//2
        groups += [s[:k+1], s[k+1:]]
    cues = []
    for g in groups:
        ws = [w["text"] for w in g]; best = None
        for k in range(1, len(ws)):
            a, b = " ".join(ws[:k]), " ".join(ws[k:]); sc = max(len(a), len(b)) + (6 if ws[k-1].lower().strip(",.") in {"a", "the", "of", "in", "to", "and", "an", "at", "on"} else 0)
            if k > 1 and ws[k-1][:1].isupper() and ws[k][:1].isupper(): sc += 14      # do not split a run of capitalised words
            if best is None or sc < best[0]: best = (sc, k)
        text = " ".join(ws)
        lines = [text] if len(text) <= max_line or best is None else [" ".join(ws[:best[1]]), " ".join(ws[best[1]:])]
        cues.append(dict(words=g, lines=lines, start=g[0]["start"], end=g[-1]["end"]))
    for i, c in enumerate(cues):
        nxt = cues[i+1]["start"]-lead if i+1 < len(cues) else c["end"]+10
        c["t0"] = max(0.0, c["start"]-lead); c["t1"] = min(c["end"]+hold, nxt-gap)
        if c["t1"]-c["t0"] < min_dur: c["t1"] = min(c["t0"]+min_dur, nxt-gap)
    return cues

def check_cues(cues, words):
    spoken = [w["text"] for c in cues for w in c["words"]]; assert spoken == [w["text"] for w in words], "cue words differ from spoken words"
    for a, b in zip(cues, cues[1:]): assert a["t1"] <= b["t0"] + 1e-6, ("overlap", a["t1"], b["t0"])
    return dict(cues=len(cues), longest_line=max(len(l) for c in cues for l in c["lines"]), shortest=round(min(c["t1"]-c["t0"] for c in cues), 2), longest=round(max(c["t1"]-c["t0"] for c in cues), 2), lines_per_cue=max(len(c["lines"]) for c in cues))

def _ts(t): h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02d}:{s:05.2f}"
def write_ass(cues, path, offset=0.0, size=46, margin_v=58):
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            f"Style: Default,DejaVu Sans,{size},&H00FFFFFF,&H000000FF,&H00101010,&H78000000,-1,0,0,0,100,100,0.5,0,1,3.4,1.2,2,200,200,{margin_v},1\n\n"
            "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    ev = "".join("Dialogue: 0,%s,%s,Default,,0,0,0,,{\\fad(110,160)}%s\n" % (_ts(c["t0"]+offset), _ts(c["t1"]+offset), "\\N".join(c["lines"])) for c in cues)
    open(path, "w", encoding="utf-8").write(head+ev)

def ebur(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    g = lambda k: float(re.findall(k+r":\s+(-?[\d.]+)", r)[-1])
    return dict(integrated_lufs=g("I"), lra=g("LRA"), true_peak_dbtp=g("Peak"))

def master_audio(src, dst, lead, total, gain_db=0.0, limit=0.84):
    """highpass, make-up gain, soft limiter, lead padding, fades, 48 kHz stereo, exact total length."""
    af = (f"pan=stereo|c0=c0|c1=c0,highpass=f=70,volume={gain_db}dB,alimiter=limit={limit}:attack=5:release=60:level=disabled,adelay={int(lead*1000)}:all=1,"
          f"apad=whole_dur={total},atrim=0:{total},afade=t=in:st={lead-0.08}:d=0.12,afade=t=out:st={total-1.6}:d=1.5,aresample=48000")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-c:a", "pcm_s16le", dst], check=True)
    return ebur(dst)
