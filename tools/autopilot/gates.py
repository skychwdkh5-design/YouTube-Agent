"""gates.py - the automatic checks between pipeline stages.

Each gate takes the production folder and returns {"ok": bool, "problems": [...], "notes": [...]}.
A gate proves a technical fact. None of them is a visual review: the `review` gate only checks that a
person-readable review was written, and it can never produce USER_APPROVED.
"""
import hashlib, json, math, os, re, struct, sys, wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LEVELS = ("TECHNICALLY_VALID", "VISUALLY_REVIEWED", "USER_APPROVED")


def _res(problems, notes=None):
    return {"ok": not problems, "problems": problems, "notes": notes or []}


def _read(path):
    with open(path, encoding="utf-8") as f: return f.read()


def _json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def voice_onset(wav_path, threshold_db=-42.0, window_s=0.02):
    """Seconds until the narration itself becomes audible (RMS onset on the narration track).
    Registry: voice-onset-measured-on-narration - a music/atmosphere bed must never hide a late voice."""
    with wave.open(wav_path, "rb") as w:
        n, ch, sw, rate = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        if sw != 2: raise ValueError("expected 16-bit PCM wav")
        raw = w.readframes(n)
    samples = struct.unpack("<%dh" % (len(raw) // 2), raw)
    step = max(1, int(rate * window_s)) * ch
    thr = 10 ** (threshold_db / 20.0)
    for i in range(0, len(samples) - step + 1, step):
        seg = samples[i:i + step]
        rms = math.sqrt(sum(s * s for s in seg) / len(seg)) / 32768.0
        if rms >= thr: return (i // ch) / rate
    return None


def topic_decision(d):
    """The decision must follow the scoring rules: it is recomputed from candidates.json and has to name the same winner."""
    import topics
    p = []
    try:
        t = _json(os.path.join(d, "research", "topic_decision.json")); c = _json(os.path.join(d, "research", "candidates.json"))
    except (OSError, ValueError) as x:
        return _res([f"cannot read research files: {x}"])
    for k in ("chosen_id", "reason", "evidence_urls", "us_hook", "mode"):
        if not t.get(k): p.append(f"topic_decision.json missing '{k}'")
    urls = t.get("evidence_urls") or []
    if not urls or not all(isinstance(u, str) and u.startswith("https://") for u in urls):
        p.append("evidence_urls must be https URLs of reliable sources")
    if t.get("mode") not in ("auto", "tie_break"): p.append("mode must be 'auto' (provable advantage) or 'tie_break' (fixed rule)")
    try:
        again = topics.run(c)
        if again["chosen_id"] != t.get("chosen_id"):
            p.append(f"the recorded choice {t.get('chosen_id')!r} is not what the scoring rules give ({again['chosen_id']!r}): re-run topics.py score")
    except (ValueError, KeyError) as x:
        p.append(f"candidates.json does not pass the scoring rules: {x}")
    return _res(p, [f"mode {t.get('mode')}: {str(t.get('reason', ''))[:120]}"])


def claims(d):
    p, notes = [], []
    path = os.path.join(d, "story", "claims.json")
    try: data = _json(path)
    except (OSError, ValueError) as x: return _res([f"cannot read claims.json: {x}"])
    cl = data.get("claims", [])
    if not cl: p.append("no claims")
    seen = set()
    for c in cl:
        cid = c.get("id", "?")
        if cid in seen: p.append(f"{cid}: duplicate id")
        seen.add(cid)
        if not c.get("text"): p.append(f"{cid}: no text")
        if c.get("used", True):
            if c.get("status") != "VERIFIED": p.append(f"{cid}: used in the video but status is {c.get('status')!r}, not VERIFIED")
            if not str(c.get("source_url", "")).startswith("https://"): p.append(f"{cid}: no https source_url")
            if not c.get("evidence_type"): p.append(f"{cid}: no evidence_type (observation / satellite-derived / model / reconstruction)")
    notes.append(f"{len(cl)} claims, {sum(1 for c in cl if c.get('used', True))} used")
    return _res(p, notes)


def script_lock(d, spoken_text_fn):
    p = []
    lock = os.path.join(d, "story", "SCRIPT_LOCK.json")
    script = os.path.join(d, "script.md")
    try:
        L = _json(lock); text = spoken_text_fn(script)
    except (OSError, ValueError) as x:
        return _res([f"cannot verify lock: {x}"])
    if L.get("spoken_sha256") != sha256_text(text):
        p.append("script.md spoken text no longer matches SCRIPT_LOCK.json (re-lock only with the owner's OK; a changed text is a new paid TTS)")
    return _res(p, [f"{len(text)} spoken characters"])


def tts_plan(d, approvals, chunk_limit):
    p, notes = [], []
    try: plan = _json(os.path.join(d, "voice", "tts_plan.json"))
    except (OSError, ValueError) as x: return _res([f"cannot read tts_plan.json: {x}"])
    if plan.get("chunk_chars_max", 0) > chunk_limit:
        p.append(f"largest chunk {plan['chunk_chars_max']} > {chunk_limit} chars (registry: tts-gateway-502-chunk-size)")
    if plan.get("blank_line_chars"):
        notes.append(f"blank lines cost {plan['blank_line_chars']} extra billable characters; script layout with single newlines is cheaper")
    a = (approvals or {}).get("tts") or {}
    if a.get("approved") and plan.get("characters", 0) > a.get("max_chars", 0):
        p.append(f"{plan['characters']} characters exceed the approved {a.get('max_chars')}")
    notes.append(f"{plan.get('characters')} billable characters in {plan.get('chunks')} chunk(s)")
    return _res(p, notes)


def tts(d):
    p, notes = [], []
    vj = os.path.join(d, "voice", "narration.voice.json")
    wav = os.path.join(d, "voice", "narration.wav")
    try: v = _json(vj)
    except (OSError, ValueError) as x: return _res([f"cannot read narration.voice.json: {x}"])
    words = v.get("words") or []
    if not v.get("timing") or not words: p.append("no provider word timings - captions would be guesses")
    if os.path.exists(wav):
        try:
            on = voice_onset(wav)
            notes.append(f"voice onset {on:.2f} s (measured on the narration track)")
            if on is None: p.append("narration is silent")
            elif on > 1.0: p.append(f"voice starts at {on:.2f} s; hook needs the voice within 1 s")
        except (OSError, ValueError, wave.Error) as x:
            notes.append(f"onset not measured: {x}")
    else:
        notes.append("narration.wav not present locally (media may live on the media/* branch); onset not measured")
    return _res(p, notes)


def captions(d):
    p = []
    try: c = _json(os.path.join(d, "captions", "captions.json"))
    except (OSError, ValueError) as x: return _res([f"cannot read captions.json: {x}"])
    val = c.get("validation", {})
    for k in ("wording_preserved", "no_overlaps", "timestamps_valid"):
        if not val.get(k): p.append(f"captions validation.{k} is not true")
    return _res(p)


def timeline(d):
    p = []
    try: t = _json(os.path.join(d, "timeline.json"))
    except (OSError, ValueError) as x: return _res([f"cannot read timeline.json: {x}"])
    if t.get("version") != 3 or t.get("profile") != "long": p.append("timeline must be version 3, profile 'long' (1920x1080)")
    if not (t.get("audio") or {}).get("voice"): p.append("timeline has no audio.voice narration")
    if not t.get("subtitles"): p.append("timeline has no subtitles block")
    if not os.path.exists(os.path.join(d, "story", "storyboard.md")): p.append("story/storyboard.md missing (a filename + zoom is not a storyboard)")
    return _res(p)


def render(d):
    p = []
    f = os.path.join(d, "final.mp4")
    if not os.path.exists(f): p.append("final.mp4 missing")
    elif os.path.getsize(f) < 100_000: p.append("final.mp4 is implausibly small")
    return _res(p)


def qc(d):
    p, notes = [], []
    try: q = _json(os.path.join(d, "qc", "qc.json"))
    except (OSError, ValueError) as x: return _res([f"cannot read qc.json: {x}"])
    if q.get("result") != "PASS": p.append(f"yt-qc result is {q.get('result')!r}")
    notes.append("TECHNICALLY_VALID only: yt-qc is an automatic check, not a visual review")
    return _res(p, notes)


def review(d):
    p = []
    try: r = _json(os.path.join(d, "qc", "review.json"))
    except (OSError, ValueError) as x: return _res([f"cannot read review.json: {x}"])
    lvl = r.get("level")
    if lvl not in LEVELS: p.append(f"level must be one of {LEVELS}")
    if lvl == "USER_APPROVED" and r.get("approved_by") != "user":
        p.append("USER_APPROVED can only be granted by the owner (approved_by must be 'user', with their message quoted in approval_quote)")
    if lvl == "USER_APPROVED" and not r.get("approval_quote"): p.append("USER_APPROVED needs approval_quote")
    if lvl in ("VISUALLY_REVIEWED", "USER_APPROVED"):
        frames = r.get("frames_reviewed") or []
        if len(frames) < 12: p.append("a visual review lists at least 12 reviewed frame timestamps (contact sheet counts only if its frames are listed)")
        if not r.get("not_verified"): p.append("not_verified must say what could NOT be checked (audio was not listened to, etc.)")
        if not r.get("defects_found_and_fixed") and not r.get("defects_none_found_reason"):
            p.append("state defects found/fixed, or why none were found")
    return _res(p, [f"level {lvl}"])


def chapters_ok(text):
    """YouTube chapter rules: first at 0:00, at least 3, each at least 10 s."""
    rows = []
    for line in text.strip().splitlines():
        m = re.match(r"^\s*(?:(\d+):)?(\d{1,2}):(\d{2})\s+\S", line)
        if not m: return ["chapter line not 'm:ss Title': " + line[:40]]
        h, mi, s = int(m.group(1) or 0), int(m.group(2)), int(m.group(3))
        rows.append(h * 3600 + mi * 60 + s)
    p = []
    if len(rows) < 3: p.append("at least 3 chapters")
    if rows and rows[0] != 0: p.append("first chapter must start at 0:00")
    if any(b - a < 10 for a, b in zip(rows, rows[1:])): p.append("every chapter must be at least 10 s")
    if rows != sorted(rows): p.append("chapters out of order")
    return p


def package(d):
    p = []
    rel = os.path.join(d, "release")
    for f in ("description.txt", "chapters.txt", "tags.txt", "COPYRIGHT_CHECK.md", "metadata.json"):
        if not os.path.exists(os.path.join(rel, f)): p.append(f"release/{f} missing")
    if p: return _res(p)
    p += chapters_ok(_read(os.path.join(rel, "chapters.txt")))
    m = _json(os.path.join(rel, "metadata.json"))
    if m.get("published") is not False: p.append("metadata.json must say published=false: the owner uploads, not the agent")
    if not m.get("title") or len(m["title"]) > 100: p.append("title missing or over 100 characters")
    if len(_read(os.path.join(rel, "tags.txt"))) > 500: p.append("tags over 500 characters")
    return _res(p)
