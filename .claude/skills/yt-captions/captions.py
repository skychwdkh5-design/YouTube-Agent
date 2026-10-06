#!/usr/bin/env python3
"""captions.py - SRT and VTT captions from word timings, cut into readable blocks.

    python3 captions.py --voice voice/narration.voice.json --out-dir captions/
    python3 captions.py --words words.json --out-dir captions/ --max-chars 84 --max-duration 6
    python3 captions.py --voice v.json --out-dir captions/ --overwrite

Input is word-level timing - the "words" list from a yt-voice metadata file, or any JSON list of
{"text", "start", "end"} (so a later forced-alignment or Whisper step can feed it too). Captions
are never built from guessed timings: no word timings, no captions.

Writes captions.srt, captions.vtt and captions.json (the cues, the settings and the validation
report) into --out-dir. Prints JSON. Exit 0 ok, 2 error.

Rules, all configurable: at most --max-chars per cue (default 84) over at most --max-lines lines
(default 2), at most --max-duration seconds (default 6.0), at least --min-duration (default 0.8)
where the gap to the next cue allows it. Cues break at sentence ends first, then at a clause mark
(, ; :) or a pause longer than --pause (default 0.6 s) once the cue is half full. Cues never
overlap, timestamps are always increasing, and the words - with their punctuation - are exactly the
spoken words in order; the validation report proves it.
"""
import json, math, os, re, sys, tempfile

SCHEMA = "yt-captions/1"
DEFAULTS = {"max_chars": 84, "max_lines": 2, "max_duration": 6.0, "min_duration": 0.8, "pause": 0.6}
# sentence and clause marks for English and the scripts most likely next; whitespace word
# splitting means languages written without spaces need word timings from the provider
SENTENCE_END = tuple(".!?…。！？؟")
CLAUSE_END = tuple(",;:—–、，；：")
CLOSERS = "\"'”’)]»"


class CaptionError(Exception):
    def __init__(self, message, status="error"):
        super().__init__(message)
        self.status = status


def load_words(path, kind):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except FileNotFoundError:
        raise CaptionError(f"not found: {path}")
    except (OSError, ValueError) as e:
        raise CaptionError(f"cannot read {path}: {type(e).__name__}: {e}")
    language = None
    if kind == "voice":
        if not isinstance(d, dict) or not str(d.get("schema", "")).startswith("yt-voice/"):
            raise CaptionError(f"{path} is not a yt-voice metadata file")
        if not d.get("timing") or not d.get("words"):
            raise CaptionError("the narration has no provider word timings; captions are not built from "
                               "guessed timings", status="no_timing")
        words, language = d["words"], d.get("language")
    else:
        words = d.get("words") if isinstance(d, dict) else d
        language = d.get("language") if isinstance(d, dict) else None
    return validate_words(words), language


def validate_words(words):
    if not isinstance(words, list) or not words:
        raise CaptionError("word list is empty or not a list")
    out = []
    for i, w in enumerate(words):
        if not isinstance(w, dict):
            raise CaptionError(f"words[{i}] is not an object")
        t, s, e = w.get("text"), w.get("start"), w.get("end")
        if not isinstance(t, str) or not t.strip() or re.search(r"\s", t.strip()):
            raise CaptionError(f"words[{i}].text must be one non-empty word")
        if "-->" in t:
            raise CaptionError(f"words[{i}] contains '-->', which would break the caption file")
        for name, v in (("start", s), ("end", e)):
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                raise CaptionError(f"words[{i}].{name} must be a finite number >= 0")
        if e < s:
            raise CaptionError(f"words[{i}] ends before it starts")
        if out and s < out[-1]["start"]:
            raise CaptionError(f"words[{i}] starts before the previous word - timings out of order")
        out.append({"text": t.strip(), "start": float(s), "end": float(e)})
    return out


def _ends(word, marks):
    return word.rstrip(CLOSERS).endswith(marks)


def chunk(words, cfg):
    """Group words into cues. Greedy, with preferred break points; never splits a word."""
    cues, cur = [], []

    def flush():
        if cur:
            cues.append({"words": list(cur)}); cur.clear()

    for i, w in enumerate(words):
        if cur:
            text_len = len(" ".join(x["text"] for x in cur))
            if (text_len + 1 + len(w["text"]) > cfg["max_chars"]
                    or w["end"] - cur[0]["start"] > cfg["max_duration"]):
                flush()
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        text_len = len(" ".join(x["text"] for x in cur))
        if nxt is None:
            break
        half = text_len >= cfg["max_chars"] / 2
        if _ends(w["text"], SENTENCE_END) and text_len >= 12:
            flush()
        elif half and (_ends(w["text"], CLAUSE_END) or nxt["start"] - w["end"] > cfg["pause"]):
            flush()
        elif nxt["start"] - w["end"] > cfg["pause"] * 2:
            flush()
    flush()

    for c in cues:
        c["text"] = " ".join(x["text"] for x in c["words"])
        c["start"], c["end"] = c["words"][0]["start"], c["words"][-1]["end"]
    # timing: no overlap, minimum duration where the gap allows, whole milliseconds
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else None
        end = max(c["end"], c["start"] + cfg["min_duration"])
        if nxt is not None:
            end = min(end, nxt)
        c["start_ms"] = int(round(c["start"] * 1000))
        c["end_ms"] = int(round(end * 1000))
    for i, c in enumerate(cues):
        if i and c["start_ms"] < cues[i - 1]["end_ms"]:
            c["start_ms"] = cues[i - 1]["end_ms"]
        if c["end_ms"] <= c["start_ms"]:
            c["end_ms"] = c["start_ms"] + 1
            if i + 1 < len(cues) and cues[i + 1]["start_ms"] < c["end_ms"]:
                cues[i + 1]["start_ms"] = c["end_ms"]
    return cues


def wrap(text, max_lines, max_chars):
    """Split a cue into at most max_lines balanced lines without breaking words."""
    if max_lines <= 1 or len(text) <= max_chars // max_lines:
        return [text]
    words = text.split(" ")
    if max_lines == 2:
        best, best_cost = [text], None
        for k in range(1, len(words)):
            a, b = " ".join(words[:k]), " ".join(words[k:])
            cost = abs(len(a) - len(b)) - (6 if _ends(words[k - 1], CLAUSE_END + SENTENCE_END) else 0)
            if best_cost is None or cost < best_cost:
                best, best_cost = [a, b], cost
        return best
    per = math.ceil(len(text) / max_lines)
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > per and len(lines) < max_lines - 1:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    return lines + [cur]


def ts(ms, sep):
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def to_srt(cues, cfg):
    blocks = []
    for i, c in enumerate(cues, 1):
        lines = wrap(c["text"], cfg["max_lines"], cfg["max_chars"])
        blocks.append(f"{i}\n{ts(c['start_ms'], ',')} --> {ts(c['end_ms'], ',')}\n" + "\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _vtt_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_vtt(cues, cfg):
    blocks = ["WEBVTT"]
    for c in cues:
        lines = wrap(c["text"], cfg["max_lines"], cfg["max_chars"])
        blocks.append(f"{ts(c['start_ms'], '.')} --> {ts(c['end_ms'], '.')}\n"
                      + "\n".join(_vtt_escape(l) for l in lines))
    return "\n\n".join(blocks) + "\n"


def validate_cues(cues, words, cfg):
    problems = []
    if " ".join(c["text"] for c in cues).split(" ") != [w["text"] for w in words]:
        problems.append("cue text is not exactly the spoken words in order")
    for i, c in enumerate(cues):
        if c["end_ms"] <= c["start_ms"]:
            problems.append(f"cue {i + 1} has no duration")
        if i and c["start_ms"] < cues[i - 1]["end_ms"]:
            problems.append(f"cue {i + 1} overlaps cue {i}")
        if len(c["words"]) > 1 and len(c["text"]) > cfg["max_chars"]:
            problems.append(f"cue {i + 1} is longer than --max-chars")
    long_single = [i + 1 for i, c in enumerate(cues) if len(c["words"]) == 1 and len(c["text"]) > cfg["max_chars"]]
    return {"wording_preserved": not any("spoken words" in p for p in problems),
            "no_overlaps": not any("overlaps" in p for p in problems),
            "timestamps_valid": not any("duration" in p for p in problems),
            "problems": problems,
            "warnings": [f"cue {n} is a single word longer than --max-chars" for n in long_single]}


def parse_srt(text):
    """Minimal SRT reader used to check what we wrote (and, later, captions from elsewhere)."""
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].strip().isdigit():
            raise CaptionError(f"bad SRT block: {block[:60]!r}")
        m = re.fullmatch(r"(\d\d):(\d\d):(\d\d),(\d{3}) --> (\d\d):(\d\d):(\d\d),(\d{3})", lines[1].strip())
        if not m:
            raise CaptionError(f"bad SRT timestamp line: {lines[1]!r}")
        g = [int(x) for x in m.groups()]
        start = ((g[0] * 60 + g[1]) * 60 + g[2]) * 1000 + g[3]
        end = ((g[4] * 60 + g[5]) * 60 + g[6]) * 1000 + g[7]
        cues.append({"start_ms": start, "end_ms": end, "text": " ".join(l.strip() for l in lines[2:])})
    return cues


def build(words, cfg, language=None):
    cues = chunk(words, cfg)
    report = validate_cues(cues, words, cfg)
    if report["problems"]:
        raise CaptionError("caption validation failed: " + "; ".join(report["problems"]), status="invalid")
    return cues, to_srt(cues, cfg), to_vtt(cues, cfg), report


def write_outputs(out_dir, srt, vtt, cues, cfg, report, language, source, overwrite):
    if not os.path.isdir(out_dir):
        raise CaptionError(f"output directory does not exist: {out_dir}")
    targets = {n: os.path.join(out_dir, n) for n in ("captions.srt", "captions.vtt", "captions.json")}
    for p in targets.values():
        if os.path.lexists(p) and not overwrite:
            raise CaptionError(f"{p} already exists; pass --overwrite to replace it", status="exists")
    meta = {"schema": SCHEMA, "language": language or "en", "source": source,
            "settings": cfg, "cue_count": len(cues),
            "duration": round(cues[-1]["end_ms"] / 1000, 3) if cues else 0,
            "validation": report,
            "cues": [{"index": i + 1, "start": c["start_ms"] / 1000, "end": c["end_ms"] / 1000,
                      "text": c["text"]} for i, c in enumerate(cues)],
            "files": {"srt": "captions.srt", "vtt": "captions.vtt"}}
    tmps = {}
    try:
        for name, content in (("captions.srt", srt), ("captions.vtt", vtt),
                              ("captions.json", json.dumps(meta, indent=1, ensure_ascii=False) + "\n")):
            fd, tmp = tempfile.mkstemp(prefix=".captions-", dir=out_dir)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            os.chmod(tmp, 0o644)
            tmps[name] = tmp
        for name, tmp in tmps.items():
            os.replace(tmp, targets[name])
    finally:
        for tmp in tmps.values():
            if os.path.exists(tmp):
                os.remove(tmp)
    return {k.split(".")[1]: v for k, v in targets.items()}


# --- CLI ---------------------------------------------------------------------------------------

def _flag(a, name):
    if name not in a: return None
    i = a.index(name)
    if i + 1 >= len(a) or a[i + 1].startswith("--"):
        raise CaptionError(f"{name} needs a value")
    return a[i + 1]


def _num(a, name, default, lo, kind=float):
    raw = _flag(a, name)
    if raw is None: return default
    try:
        v = kind(raw)
    except ValueError:
        raise CaptionError(f"{name} expects a number, got {raw!r}")
    if not math.isfinite(v) or v < lo:
        raise CaptionError(f"{name} must be a finite number >= {lo}, got {raw!r}")
    return v


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0
    try:
        valued = {"--voice", "--words", "--out-dir", "--language", "--max-chars", "--max-lines",
                  "--max-duration", "--min-duration", "--pause"}
        vals = {i + 1 for i, x in enumerate(a[:-1]) if x in valued}
        unknown = [x for i, x in enumerate(a) if i not in vals and x not in valued | {"--overwrite"}]
        if unknown: raise CaptionError(f"unknown argument(s): {unknown}")
        cfg = {"max_chars": _num(a, "--max-chars", DEFAULTS["max_chars"], 10, int),
               "max_lines": _num(a, "--max-lines", DEFAULTS["max_lines"], 1, int),
               "max_duration": _num(a, "--max-duration", DEFAULTS["max_duration"], 0.5),
               "min_duration": _num(a, "--min-duration", DEFAULTS["min_duration"], 0),
               "pause": _num(a, "--pause", DEFAULTS["pause"], 0)}
        if cfg["max_lines"] > 3: raise CaptionError("--max-lines must be 1, 2 or 3")
        if cfg["min_duration"] > cfg["max_duration"]:
            raise CaptionError("--min-duration cannot be longer than --max-duration")
        voice, wfile = _flag(a, "--voice"), _flag(a, "--words")
        if bool(voice) == bool(wfile): raise CaptionError("give exactly one of --voice or --words")
        out_dir = _flag(a, "--out-dir")
        if not out_dir: raise CaptionError("--out-dir is required")
        words, language = load_words(voice or wfile, "voice" if voice else "words")
        language = _flag(a, "--language") or language or "en"
        if not re.fullmatch(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*", language):
            raise CaptionError(f"--language must be a BCP 47 tag like en or en-US, got {language!r}")
        cues, srt, vtt, report = build(words, cfg, language)
        files = write_outputs(os.path.abspath(out_dir), srt, vtt, cues, cfg, report, language,
                              os.path.basename(voice or wfile), "--overwrite" in a)
        print(json.dumps({"status": "ok", "files": files, "cues": len(cues), "language": language,
                          "duration": round(cues[-1]["end_ms"] / 1000, 3),
                          "validation": report}, indent=1, ensure_ascii=False))
        return 0
    except CaptionError as e:
        print(json.dumps({"status": e.status, "error": str(e)}, indent=1, ensure_ascii=False))
        return 2
    except Exception as e:  # never a traceback
        print(json.dumps({"status": "error", "error": f"unexpected {type(e).__name__}: {e}"}, indent=1))
        return 2


if __name__ == "__main__":
    sys.exit(main())
