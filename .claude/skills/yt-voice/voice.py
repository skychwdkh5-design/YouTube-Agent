#!/usr/bin/env python3
"""voice.py - narration audio from a script, through an interchangeable TTS provider.

    python3 voice.py --script script.md --voice-id VOICE --output voice/narration.wav     # plan only
    python3 voice.py --script script.md --voice-id VOICE --output voice/narration.wav --confirm
    python3 voice.py --text "One line." --voice-id VOICE --output n.wav --confirm --max-chars 500

Every command prints JSON. Without --confirm nothing is sent anywhere: you get the spoken text,
its character count and the request plan. With --confirm the text goes to the provider (a PAID
request) only if it is under --max-chars (default 3000).

Providers: elevenlabs (ELEVENLABS_API_KEY, or --auth proxy / YT_VOICE_AUTH=proxy when the key is a
network secret the session's egress proxy adds to requests). A new provider is one class in PROVIDERS with a
synthesize() method; the output format below does not change.

Output:
  <output>             narration audio (.wav PCM 16-bit, or .mp3), built with the local ffmpeg
  <stem>.voice.json    metadata - provider, voice, model, the exact spoken text, chunk offsets,
                       and word timings when the provider returned alignment (schema yt-voice/1)

Audio and metadata are written to temporary files and renamed into place only after the whole
generation succeeded, so a failure never leaves a finished-looking narration. Existing files are
not replaced without --overwrite. The API key is read from the environment only and is never
printed, logged or written to disk.
"""
import base64, hashlib, json, math, os, re, shutil, subprocess, sys, tempfile, time, wave
import urllib.error, urllib.request

SCHEMA = "yt-voice/1"
UA = "YouTube-Agent-yt-voice/1.0"
DEFAULTS = {"max_chars": 3000, "max_chunk_chars": 2500, "timeout_s": 120}
AUDIO_EXT = (".wav", ".mp3")


class VoiceError(Exception):
    def __init__(self, message, status="error", **extra):
        super().__init__(message)
        self.status = status
        self.extra = extra


def _redact(text, secrets):
    text = str(text)
    for s in secrets:
        if s and len(s) > 3:
            text = text.replace(s, "[REDACTED]")
    return text


# --- script -> spoken text ---------------------------------------------------------------------

DIRECTION = re.compile(r"\[[^\]\n]*\]")          # [ON SCREEN: ...], [B-ROLL], [pause] ...
LIST_MARK = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


def spoken_text(raw, keep_markup=False):
    """Turn a yt-script script into what is actually said. Removes headings, [bracketed]
    directions, list markers and **bold**/__bold__ markers; keeps every spoken word and its
    punctuation. Returns (text, removed) - removed lists what was dropped, for review."""
    if keep_markup:
        text = re.sub(r"[ \t]+", " ", raw.strip())
        return re.sub(r"\n{3,}", "\n\n", text), []
    removed, paras, cur = [], [], []
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("#") or re.fullmatch(r"[-*_=]{3,}", s or "x"):
            if s: removed.append(s)
            if cur: paras.append(" ".join(cur)); cur = []
            continue
        removed += DIRECTION.findall(s)
        s = DIRECTION.sub(" ", s)
        s = LIST_MARK.sub("", s).replace("**", "").replace("__", "")
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            cur.append(s)
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur: paras.append(" ".join(cur))
    return "\n\n".join(paras), removed


def split_chunks(text, limit):
    """Split at paragraph, then sentence, then word boundaries so no chunk exceeds limit."""
    chunks = []
    for para in text.split("\n\n"):
        if len(para) <= limit:
            chunks.append(para); continue
        cur = ""
        for sent in re.split(r"(?<=[.!?…])\s+", para):
            for piece in ([sent] if len(sent) <= limit else _by_words(sent, limit)):
                if cur and len(cur) + 1 + len(piece) > limit:
                    chunks.append(cur); cur = piece
                else:
                    cur = f"{cur} {piece}" if cur else piece
        if cur: chunks.append(cur)
    # merge small neighbours back together to keep the number of requests down
    merged = []
    for c in chunks:
        if merged and len(merged[-1]) + 2 + len(c) <= limit:
            merged[-1] = merged[-1] + "\n\n" + c
        else:
            merged.append(c)
    return merged


def _by_words(sent, limit):
    out, cur = [], ""
    for w in sent.split(" "):
        if len(w) > limit:
            raise VoiceError(f"a single word is longer than --max-chunk-chars {limit}")
        if cur and len(cur) + 1 + len(w) > limit:
            out.append(cur); cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur: out.append(cur)
    return out


# --- providers ---------------------------------------------------------------------------------

class Provider:
    """Interface. synthesize() returns {"audio": bytes, "format": "mp3"|"wav",
    "alignment": {"characters": [...], "start": [...], "end": [...]} or None}."""
    name = "base"
    env_key = None

    def __init__(self, options):
        self.options = options

    def secrets(self):
        return [os.environ.get(self.env_key, "")] if self.env_key else []

    def auth_mode(self):
        """'env' sends the key from env_key; 'proxy' sends no key - the session's egress proxy adds
        the credential (a configured network secret), so the key never enters this process."""
        mode = (self.options.get("auth") or os.environ.get("YT_VOICE_AUTH") or "env").strip()
        if mode not in ("env", "proxy"):
            raise VoiceError(f"--auth must be 'env' or 'proxy', got {mode!r}")
        return mode

    def check_ready(self):
        if self.auth_mode() == "env" and self.env_key and not os.environ.get(self.env_key, "").strip():
            raise VoiceError(f"missing environment variable: {self.env_key} (or pass --auth proxy if the "
                             "credential is configured as a network secret)", status="missing_credentials")

    def describe(self):
        return {"provider": self.name}

    def synthesize(self, text, voice_id):
        raise NotImplementedError


class ElevenLabs(Provider):
    name = "elevenlabs"
    env_key = "ELEVENLABS_API_KEY"
    api = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps"
    default_model = "eleven_multilingual_v2"
    default_format = "mp3_44100_128"

    def describe(self):
        return {"provider": self.name, "model_id": self.options.get("model") or self.default_model,
                "output_format": self.default_format, "endpoint": self.api.split("{")[0] + "{voice_id}/with-timestamps"}

    def synthesize(self, text, voice_id):
        key = os.environ.get(self.env_key, "").strip() if self.auth_mode() == "env" else ""
        body = {"text": text, "model_id": self.options.get("model") or self.default_model}
        if self.options.get("language_code"):
            body["language_code"] = self.options["language_code"]
        url = self.api.format(voice=voice_id) + "?output_format=" + self.default_format
        headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": UA}
        if key:
            headers["xi-api-key"] = key
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers=headers)
        secrets = [key]
        try:
            with urllib.request.urlopen(req, timeout=self.options.get("timeout_s", 120)) as r:
                raw = r.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            try:
                d = json.loads(detail).get("detail")
                detail = (d.get("message") or d.get("status")) if isinstance(d, dict) else str(d)
            except (ValueError, AttributeError):
                pass
            hint = {401: " (API key rejected or missing a permission)", 402: " (payment required)", 429: " (rate limit or quota)"}
            raise VoiceError(_redact(f"elevenlabs HTTP {e.code}{hint.get(e.code, '')}: {detail}", secrets),
                             status="provider_error")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise VoiceError(_redact(f"elevenlabs network error: {type(e).__name__}: {e}", secrets),
                             status="network_error")
        try:
            d = json.loads(raw)
            audio = base64.b64decode(d["audio_base64"], validate=True)
        except (ValueError, KeyError, TypeError) as e:
            raise VoiceError(f"elevenlabs returned a malformed response ({type(e).__name__})",
                             status="malformed_response")
        if not audio:
            raise VoiceError("elevenlabs returned empty audio", status="malformed_response")
        a = d.get("alignment")
        alignment = None
        if isinstance(a, dict):
            alignment = {"characters": a.get("characters"), "start": a.get("character_start_times_seconds"),
                         "end": a.get("character_end_times_seconds")}
        return {"audio": audio, "format": "mp3", "alignment": alignment}


PROVIDERS = {"elevenlabs": ElevenLabs}


# --- timing ------------------------------------------------------------------------------------

def words_from_alignment(text, alignment, offset):
    """Word timings from per-character alignment. Returns None - never a guess - if the
    alignment does not describe exactly this text with sane, increasing times."""
    if not alignment:
        return None
    chars, st, en = alignment.get("characters"), alignment.get("start"), alignment.get("end")
    if not (isinstance(chars, list) and isinstance(st, list) and isinstance(en, list)):
        return None
    if not (len(chars) == len(st) == len(en)) or "".join(map(str, chars)) != text:
        return None
    try:
        st, en = [float(x) for x in st], [float(x) for x in en]
    except (TypeError, ValueError):
        return None
    if any(not (math.isfinite(a) and math.isfinite(b)) or a < 0 or b < a for a, b in zip(st, en)):
        return None
    words = []
    for m in re.finditer(r"\S+", text):
        s, e = m.start(), m.end() - 1
        words.append({"text": m.group(), "start": round(st[s] + offset, 3), "end": round(en[e] + offset, 3)})
    for a, b in zip(words, words[1:]):
        if b["start"] < a["start"]:
            return None
    return words


# --- audio assembly (local ffmpeg) -------------------------------------------------------------

def _run(cmd, timeout=300):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise VoiceError(f"{cmd[0]} is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        raise VoiceError(f"{cmd[0]} timed out")
    if r.returncode != 0:
        raise VoiceError(f"{cmd[0]} failed: {r.stderr.strip()[-300:]}", status="audio_error")
    return r


def to_wav(src, dst, rate=44100):
    _run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y", "-i", src,
          "-ac", "1", "-ar", str(rate), "-c:a", "pcm_s16le", "-map_metadata", "-1",
          "-fflags", "+bitexact", "-flags:a", "+bitexact", dst])


def wav_duration(path):
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def join_wavs(parts, dst):
    with wave.open(parts[0], "rb") as first:
        params = first.getparams()
    with wave.open(dst, "wb") as out:
        out.setparams(params)
        for p in parts:
            with wave.open(p, "rb") as w:
                if w.getparams()[:3] != params[:3]:
                    raise VoiceError("chunk audio formats differ", status="audio_error")
                out.writeframes(w.readframes(w.getnframes()))


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# --- generation --------------------------------------------------------------------------------

def plan(text, provider_name, voice_id, output, options):
    if provider_name not in PROVIDERS:
        raise VoiceError(f"unknown provider {provider_name!r}; available: {sorted(PROVIDERS)}")
    if not re.fullmatch(r"[A-Za-z0-9_-]{4,64}", voice_id or ""):
        raise VoiceError("--voice-id must be 4-64 letters, digits, '-' or '_'")
    if not text.strip():
        raise VoiceError("the script has no spoken text")
    if not output.lower().endswith(AUDIO_EXT):
        raise VoiceError(f"--output must end in {' or '.join(AUDIO_EXT)}")
    chunks = split_chunks(text, options["max_chunk_chars"])
    billed = sum(len(c) for c in chunks)
    if billed > options["max_chars"]:
        raise VoiceError(f"{billed} characters is over --max-chars {options['max_chars']}; nothing was "
                         "sent. Raise --max-chars only if this cost is intended", status="over_limit",
                         characters=billed)
    provider = PROVIDERS[provider_name](options)
    return {"provider": provider, "voice_id": voice_id, "text": text, "chunks": chunks,
            "characters": billed, "output": os.path.abspath(output)}


def meta_path(output):
    return os.path.splitext(output)[0] + ".voice.json"


def generate(p, options, overwrite=False):
    out, provider = p["output"], p["provider"]
    meta = meta_path(out)
    if not os.path.isdir(os.path.dirname(out)):
        raise VoiceError(f"output directory does not exist: {os.path.dirname(out)}")
    for f in (out, meta):
        if os.path.lexists(f) and not overwrite:
            raise VoiceError(f"{f} already exists; pass --overwrite to replace it", status="exists")
    provider.check_ready()
    work = tempfile.mkdtemp(prefix=".voice-", dir=os.path.dirname(out))
    try:
        parts, chunk_info, words, timing_ok, offset = [], [], [], True, 0.0
        for i, text in enumerate(p["chunks"]):
            res = provider.synthesize(text, p["voice_id"])
            raw = os.path.join(work, f"chunk{i}.{res['format']}")
            with open(raw, "wb") as f:
                f.write(res["audio"])
            wav = os.path.join(work, f"chunk{i}.wav")
            to_wav(raw, wav)
            dur = wav_duration(wav)
            if dur <= 0:
                raise VoiceError(f"chunk {i} decoded to no audio", status="malformed_response")
            w = words_from_alignment(text, res.get("alignment"), offset)
            if w is None:
                timing_ok = False
            else:
                words += w
            chunk_info.append({"index": i, "characters": len(text), "offset": round(offset, 3),
                               "duration": round(dur, 3), "timing": w is not None})
            parts.append(wav)
            offset += dur
        joined = os.path.join(work, "narration.wav")
        join_wavs(parts, joined)
        final_tmp = joined
        if out.lower().endswith(".mp3"):
            final_tmp = os.path.join(work, "narration.mp3")
            _run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y", "-i", joined,
                  "-c:a", "libmp3lame", "-b:a", "192k", "-map_metadata", "-1", final_tmp])
        duration = wav_duration(joined)
        warnings = [] if timing_ok else [
            "provider timing was missing or did not match the text for at least one chunk; "
            "no word timings are kept - captions need another timing source"]
        md = {"schema": SCHEMA, **provider.describe(), "voice_id": p["voice_id"],
              "language": options.get("language") or "en",
              "audio": os.path.basename(out), "audio_format": os.path.splitext(out)[1][1:],
              "audio_sha256": _sha256(final_tmp), "duration": round(duration, 3),
              "characters": p["characters"], "text": "\n\n".join(p["chunks"]),
              "text_sha256": hashlib.sha256("\n\n".join(p["chunks"]).encode()).hexdigest(),
              "chunks": chunk_info,
              "timing": ({"source": "provider", "unit": "seconds", "level": "word"} if timing_ok else None),
              "words": words if timing_ok else [],
              "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "warnings": warnings}
        meta_tmp = os.path.join(work, "voice.json")
        with open(meta_tmp, "w", encoding="utf-8") as f:
            json.dump(md, f, indent=1, ensure_ascii=False)
        os.replace(final_tmp, out)
        try:
            os.replace(meta_tmp, meta)
        except OSError:
            os.remove(out)
            raise
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return {"status": "ok", "output": out, "metadata": meta, "duration": md["duration"],
            "characters": md["characters"], "chunks": len(chunk_info),
            "timing": md["timing"] is not None, "words": len(md["words"]), "warnings": warnings}


# --- CLI ---------------------------------------------------------------------------------------

def _flag(a, name):
    if name not in a: return None
    i = a.index(name)
    if i + 1 >= len(a) or (a[i + 1].startswith("--") and name != "--text"):
        raise VoiceError(f"{name} needs a value")
    return a[i + 1]


def _int(a, name, default, lo):
    raw = _flag(a, name)
    if raw is None: return default
    try:
        v = int(raw)
    except ValueError:
        raise VoiceError(f"{name} expects an integer, got {raw!r}")
    if v < lo: raise VoiceError(f"{name} must be >= {lo}, got {v}")
    return v


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0
    secrets = lambda: [os.environ.get(c.env_key, "") for c in PROVIDERS.values() if c.env_key]
    try:
        valued = {"--script", "--text", "--provider", "--voice-id", "--output", "--model", "--language",
                  "--max-chars", "--max-chunk-chars", "--timeout", "--auth"}
        flags = {"--confirm", "--overwrite", "--keep-markup"}
        vals = {i + 1 for i, x in enumerate(a[:-1]) if x in valued}
        unknown = [x for i, x in enumerate(a) if x.startswith("--") and i not in vals and x not in valued | flags]
        if unknown: raise VoiceError(f"unknown option(s): {unknown}")
        options = {"max_chars": _int(a, "--max-chars", DEFAULTS["max_chars"], 1),
                   "max_chunk_chars": _int(a, "--max-chunk-chars", DEFAULTS["max_chunk_chars"], 50),
                   "timeout_s": _int(a, "--timeout", DEFAULTS["timeout_s"], 1),
                   "model": _flag(a, "--model"), "language": _flag(a, "--language") or "en",
                   "auth": _flag(a, "--auth")}
        if options["language"] != "en":
            options["language_code"] = options["language"]
        script, raw_text = _flag(a, "--script"), _flag(a, "--text")
        if bool(script) == bool(raw_text):
            raise VoiceError("give exactly one of --script FILE or --text \"...\"")
        if script:
            try:
                with open(script, encoding="utf-8") as f:
                    raw_text = f.read()
            except OSError as e:
                raise VoiceError(f"cannot read script: {type(e).__name__}: {e}")
        text, removed = spoken_text(raw_text, "--keep-markup" in a)
        output = _flag(a, "--output")
        if not output: raise VoiceError("--output is required")
        p = plan(text, _flag(a, "--provider") or "elevenlabs", _flag(a, "--voice-id"), output, options)
        if "--confirm" not in a:
            raise VoiceError("generation is a paid request and needs --confirm; nothing was sent",
                             status="confirm_required", characters=p["characters"],
                             chunks=len(p["chunks"]), **p["provider"].describe(),
                             removed_from_script=removed, spoken_text=text)
        result = generate(p, options, "--overwrite" in a)
        result["removed_from_script"] = removed
        print(json.dumps(result, indent=1, ensure_ascii=False))
        return 0
    except VoiceError as e:
        out = {"status": e.status, "error": _redact(str(e), secrets()), **e.extra}
        print(_redact(json.dumps(out, indent=1, ensure_ascii=False, default=str), secrets()))
        return 2
    except Exception as e:  # never a traceback, never a key
        print(json.dumps({"status": "error",
                          "error": _redact(f"unexpected {type(e).__name__}: {e}", secrets())}, indent=1))
        return 2


if __name__ == "__main__":
    sys.exit(main())
