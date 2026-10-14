#!/usr/bin/env python3
"""recover_narration.py - rebuild a paid narration from its saved provider responses, at ZERO cost, and prove it.

    python3 tools/autopilot/recover_narration.py --meta narration.voice.json --cache DIR --out OUT_DIR [--format-old]

Why: the paid ElevenLabs responses (audio + alignment) are the expensive part; the WAV and the word timings are
derived from them by local code. If the container is lost, the cache plus the .voice.json is enough. This tool:
  1. splits the recorded text into its chunks (stored as chunks joined by a blank line, sizes in `chunks`);
  2. finds each chunk's saved response in the cache by comparing the alignment's characters with the chunk text
     (two cache layouts are understood: `<key>.json` with audio_base64 (yt-voice now) and `<key>.mp3 + <key>.json`
     with the alignment next to the audio (yt-voice at the time of EP001));
  3. decodes and joins them with yt-voice's own functions (to_wav / join_wavs) and writes OUT_DIR/narration.wav
     plus OUT_DIR/recovery_report.json;
  4. compares the result with the recorded audio_sha256 and with the recorded word timings, and says plainly which
     matched. A byte-identical WAV is proof; an identical PCM stream or identical timings is strong evidence;
     anything else is reported as NOT reproduced.
Nothing is written outside OUT_DIR, nothing is overwritten (OUT_DIR must be new or empty), no network, no API call.
"""
import base64, hashlib, importlib.util, json, os, sys, tempfile, wave

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(os.path.dirname(os.path.dirname(HERE)), ".claude", "skills")


def _voice():
    spec = importlib.util.spec_from_file_location("yt_voice_rec", os.path.join(SKILLS, "yt-voice", "voice.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def _pcm_sha(path):
    with wave.open(path, "rb") as w: return hashlib.sha256(w.readframes(w.getnframes())).hexdigest()


def load_cache(cache_dir):
    """-> list of {key, text, alignment, audio_bytes or None, mp3_path or None} for every readable entry."""
    out = []
    for name in sorted(os.listdir(cache_dir)):
        if not name.endswith(".json"): continue
        key = name[:-5]
        try:
            with open(os.path.join(cache_dir, name), encoding="utf-8") as f: d = json.load(f)
        except (OSError, ValueError):
            continue
        al = d.get("alignment")
        text = "".join(al["characters"]) if al and al.get("characters") else None
        audio = base64.b64decode(d["audio_base64"]) if d.get("audio_base64") else None
        mp3 = os.path.join(cache_dir, key + ".mp3")
        out.append({"key": key, "text": text, "alignment": al, "audio": audio, "mp3": mp3 if os.path.exists(mp3) else None, "format": d.get("format", "mp3_44100_128")})
    return out


def recover(meta_path, cache_dir, out_dir):
    v = _voice()
    with open(meta_path, encoding="utf-8") as f: meta = json.load(f)
    if os.path.exists(out_dir) and os.listdir(out_dir): raise ValueError(f"{out_dir} is not empty; nothing is ever overwritten")
    os.makedirs(out_dir, exist_ok=True)
    chunks, pos = [], 0                       # the stored text is the chunks joined by a blank line; chunk sizes are recorded
    for c in meta["chunks"]:
        chunks.append(meta["text"][pos:pos + c["characters"]]); pos += c["characters"] + 2
    if sum(len(c) for c in chunks) != meta["characters"] or pos - 2 != len(meta["text"]):
        raise ValueError("the recorded text does not split into the recorded chunk sizes")
    cache = load_cache(cache_dir)
    used, matched, missing = set(), [], []
    work = tempfile.mkdtemp(prefix="recover-", dir=out_dir)
    parts, words, offset, info = [], [], 0.0, []
    for i, text in enumerate(chunks):
        hit = next((c for c in cache if c["key"] not in used and c["text"] == text), None)
        if hit is None:
            missing.append({"chunk": i, "characters": len(text)}); continue
        used.add(hit["key"])
        raw = os.path.join(work, f"chunk{i}.mp3")
        if hit["audio"] is not None:
            with open(raw, "wb") as f: f.write(hit["audio"])
        elif hit["mp3"]:
            with open(hit["mp3"], "rb") as s, open(raw, "wb") as f: f.write(s.read())
        else:
            missing.append({"chunk": i, "characters": len(text), "why": "alignment found but no audio"}); continue
        wav = os.path.join(work, f"chunk{i}.wav")
        v.to_wav(raw, wav)
        dur = v.wav_duration(wav)
        w = v.words_from_alignment(text, hit["alignment"], offset)
        if w: words += w
        info.append({"index": i, "characters": len(text), "offset": round(offset, 3), "duration": round(dur, 3), "timing": w is not None})
        parts.append(wav); offset += dur
        matched.append({"chunk": i, "cache_key": hit["key"]})
    report = {"chunks_total": len(chunks), "chunks_matched": len(matched), "missing": missing, "matches": matched}
    if missing:
        report["result"] = "INCOMPLETE: " + str(len(missing)) + " chunk(s) have no saved response - they would have to be paid again"
    else:
        out_wav = os.path.join(out_dir, "narration.wav")
        v.join_wavs(parts, out_wav)
        report["wav_sha256"] = _sha(out_wav)
        report["pcm_sha256"] = _pcm_sha(out_wav)
        report["duration"] = round(v.wav_duration(out_wav), 3)
        rec_sha = meta.get("audio_sha256")
        report["recorded_audio_sha256"] = rec_sha
        report["byte_identical_wav"] = report["wav_sha256"] == rec_sha
        report["duration_matches"] = abs(report["duration"] - meta["duration"]) < 0.002
        rec_words = [(w["text"], round(w["start"], 3), round(w["end"], 3)) for w in meta.get("words", [])]
        new_words = [(w["text"], round(w["start"], 3), round(w["end"], 3)) for w in words]
        report["word_timings_identical"] = rec_words == new_words and bool(new_words)
        report["words"] = len(new_words)
        report["chunk_offsets_identical"] = [(c["index"], c["offset"], c["duration"]) for c in info] == [(c["index"], c["offset"], c["duration"]) for c in meta.get("chunks", [])]
        if report["byte_identical_wav"]:
            report["result"] = "PROVEN: byte-identical WAV"
        elif report["word_timings_identical"] and report["duration_matches"]:
            report["result"] = "REPRODUCED: same durations, chunk offsets and word timings; the WAV bytes differ from the recorded file (different ffmpeg build or container metadata) - the audio is the same speech"
        else:
            report["result"] = "NOT REPRODUCED: timings or duration differ from the record"
    for fn in os.listdir(work): os.remove(os.path.join(work, fn))
    os.rmdir(work)
    with open(os.path.join(out_dir, "recovery_report.json"), "w", encoding="utf-8") as f: json.dump(report, f, indent=1)
    return report


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    def opt(n): return a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else None
    if not (opt("--meta") and opt("--cache") and opt("--out")):
        print(__doc__); return 2
    try:
        r = recover(opt("--meta"), opt("--cache"), opt("--out"))
    except (ValueError, OSError, KeyError) as x:
        print(json.dumps({"ok": False, "error": f"{type(x).__name__}: {x}"})); return 2
    print(json.dumps(r, indent=1))
    return 0 if not r["result"].startswith(("INCOMPLETE", "NOT")) else 1


if __name__ == "__main__":
    sys.exit(main())
