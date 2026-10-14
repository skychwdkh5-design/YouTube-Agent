#!/usr/bin/env python3
"""orbital.py - one pipeline from topic research to a publication package, with state, gates and bounded retries.

    python3 tools/autopilot/orbital.py preflight
    python3 tools/autopilot/orbital.py init SLUG
    python3 tools/autopilot/orbital.py status SLUG            # every stage: done / ready / agent_todo / needs_approval / blocked / stale / gate_failed
    python3 tools/autopilot/orbital.py next SLUG              # the one thing to do now
    python3 tools/autopilot/orbital.py run SLUG [--stage ID] [--confirm]   # runs the next free automatic stage
    python3 tools/autopilot/orbital.py complete SLUG ID       # record an agent stage after its gate passes
    python3 tools/autopilot/orbital.py lock SLUG              # write SCRIPT_LOCK.json from script.md
    python3 tools/autopilot/orbital.py approve SLUG tts --max-chars N --quote "owner's words"
    python3 tools/autopilot/orbital.py ledger SLUG            # paid requests made for this video

Everything prints JSON. Rules this tool enforces (each traces to tools/memory + knowledge/solutions.json):
 - paid stages (ElevenLabs) run only with an owner approval recorded in approvals.json AND --confirm, once,
   with a persistent chunk cache, and are never retried automatically;
 - free stages are retried at most `max_attempts` times, only for transient failures, with backoff;
 - every failure is matched against the solutions registry and the diagnosis is saved in state.json;
 - there is no publish stage - the owner uploads;
 - gates prove technical facts only; the highest level the tool can reach is TECHNICALLY_VALID.
"""
import datetime, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILLS = os.path.join(ROOT, ".claude", "skills")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "memory"))
import gates  # noqa: E402
import kb  # noqa: E402

with open(os.path.join(HERE, "pipeline.json"), encoding="utf-8") as _f:
    PIPELINE = json.load(_f)
STAGES = {s["id"]: s for s in PIPELINE["stages"]}
ORDER = [s["id"] for s in PIPELINE["stages"]]
LIMITS = PIPELINE["limits"]
TRANSIENT = re.compile(r"timed? ?out|connection (reset|aborted|refused)|temporar|HTTP 5\d\d|502|503|504|broken pipe|\.part\.mp4", re.I)


def prod_root():
    return os.environ.get("ORBITAL_PRODUCTIONS") or os.path.join(ROOT, "productions")


def pdir(slug):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", slug or ""):
        raise ValueError("slug must be kebab-case, e.g. ep003-lake-mead")
    return os.path.join(prod_root(), slug)


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError):
        return default


def _read(path):
    with open(path, encoding="utf-8") as f: return f.read()


def _save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False); f.write("\n")
    os.replace(tmp, path)


def _voice_module():
    spec = importlib.util.spec_from_file_location("yt_voice", os.path.join(SKILLS, "yt-voice", "voice.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def spoken_text(script_path):
    with open(script_path, encoding="utf-8") as f: raw = f.read()
    return _voice_module().spoken_text(raw, False)[0]


# ---------------------------------------------------------------- gates
def run_gate(stage, d):
    g, approvals = stage.get("gate"), _load(os.path.join(d, "approvals.json"), {})
    if g == "topic_decision": return gates.topic_decision(d)
    if g == "claims": return gates.claims(d)
    if g == "script_lock": return gates.script_lock(d, spoken_text)
    if g == "tts_plan": return gates.tts_plan(d, approvals, LIMITS["tts_chunk_chars"])
    if g == "tts": return gates.tts(d)
    if g == "captions": return gates.captions(d)
    if g == "timeline": return gates.timeline(d)
    if g == "render": return gates.render(d)
    if g == "qc": return gates.qc(d)
    if g == "review": return gates.review(d)
    if g == "package": return gates.package(d)
    return {"ok": True, "problems": [], "notes": []}


def _inputs_sha(stage, d):
    h = hashlib.sha256()
    for need in stage["needs"]:
        for o in STAGES[need]["outputs"]:
            p = os.path.join(d, o)
            h.update((o + ":" + (gates.sha256_file(p) if os.path.isfile(p) else "-")).encode())
    return h.hexdigest()


# ---------------------------------------------------------------- status
def status(slug):
    d = pdir(slug)
    if not os.path.isdir(d): raise ValueError(f"no production folder: productions/{slug} (run: init {slug})")
    state = _load(os.path.join(d, "state.json"), {"stages": {}})
    approvals = _load(os.path.join(d, "approvals.json"), {})
    out, done = [], set()
    for sid in ORDER:
        s = STAGES[sid]
        have = [o for o in s["outputs"] if os.path.exists(os.path.join(d, o))]
        row = {"stage": sid, "kind": s["kind"], "cost": s.get("cost", "none")}
        unmet = [n for n in s["needs"] if n not in done]
        rec = state["stages"].get(sid, {})
        if unmet:                                    # an upstream stage is not done: nothing downstream can be
            row["state"] = "blocked"; row["blocked_by"] = unmet
            if len(have) == len(s["outputs"]): row["note"] = "outputs exist but an upstream stage is not done"
        elif len(have) == len(s["outputs"]):
            g = run_gate(s, d)
            row["gate"] = g
            if not g["ok"]: row["state"] = "gate_failed"
            elif rec.get("inputs_sha") and rec["inputs_sha"] != _inputs_sha(s, d): row["state"] = "stale"
            else:
                row["state"] = "done"; done.add(sid)
        elif s["kind"] == "agent":
            row["state"] = "agent_todo"; row["skill"] = s.get("skill"); row["how"] = s.get("how")
        elif s.get("cost") == "paid" and not (approvals.get(sid) or {}).get("approved"):
            row["state"] = "needs_approval"
        else:
            row["state"] = "ready"
        if rec.get("last_failure"): row["last_failure"] = rec["last_failure"]
        row["missing_outputs"] = [o for o in s["outputs"] if o not in have]
        out.append(row)
    nxt = next((r for r in out if r["state"] != "done"), None)
    return {"slug": slug, "stages": out, "next": nxt and {"stage": nxt["stage"], "state": nxt["state"], "kind": nxt["kind"]},
            "level": "TECHNICALLY_VALID" if all(r["state"] == "done" for r in out if r["stage"] in ("qc",)) and any(r["stage"] == "qc" and r["state"] == "done" for r in out) else None}


# ---------------------------------------------------------------- execution
def execute(cmd, cwd, retryable, env_extra=None, allow_autofix=True):
    """Run a command with bounded retries. Returns {ok, attempts:[...], diagnosis:[...], applied_fix}.
    A failure is matched against the registry; a matching entry that carries an `auto_fix` (environment only, whitelisted
    in kb.py) is applied ONCE and the command retried. Paid stages pass allow_autofix=False."""
    env = dict(os.environ, **(env_extra or {}))
    max_attempts = LIMITS["max_attempts"] if retryable else 1
    attempts, applied = [], None
    n = 0
    while True:
        n += 1
        t0 = time.time()
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
        a = {"n": n, "rc": r.returncode, "seconds": round(time.time() - t0, 1)}
        attempts.append(a)
        if r.returncode == 0:
            return {"ok": True, "attempts": attempts, "stdout": r.stdout, **({"applied_fix": applied} if applied else {})}
        text = (r.stdout + "\n" + r.stderr)[-4000:]
        a["tail"] = text[-600:]
        a["diagnosis"] = kb.diagnose(text)
        fix = next((d for d in a["diagnosis"] if d.get("auto_fix")), None) if allow_autofix and not applied else None
        if fix:
            env.update({k: v.format(root=ROOT) for k, v in fix["auto_fix"]["env"].items()})
            applied = {"entry": fix["id"], "env_keys": sorted(fix["auto_fix"]["env"])}
            continue                                         # one extra attempt, not counted against max_attempts
        if n - (1 if applied else 0) < max_attempts and TRANSIENT.search(text):
            time.sleep(LIMITS["retry_backoff_s"][min(n - 1, len(LIMITS["retry_backoff_s"]) - 1)])
            continue
        break
    return {"ok": False, "attempts": attempts, "stdout": r.stdout, "diagnosis": attempts[-1].get("diagnosis", []),
            "retried": len(attempts) > 1, **({"applied_fix": applied} if applied else {}),
            "retry_policy": "transient failures only, at most %d attempts" % max_attempts if retryable else "never retried automatically"}


def _auth_args():
    return [] if os.environ.get("ELEVENLABS_API_KEY") else ["--auth", "proxy"]


def stage_command(sid, d, overwrite=False):
    py = sys.executable
    ow = ["--overwrite"] if overwrite else []
    if sid == "captions":
        return [py, os.path.join(SKILLS, "yt-captions", "captions.py"), "--voice", "voice/narration.voice.json", "--out-dir", "captions"] + ow
    if sid == "render":
        return [py, os.path.join(SKILLS, "yt-render", "render.py"), "--timeline", "timeline.json", "--output", "final.mp4", "--confirm"] + ow
    if sid == "qc":
        return [py, os.path.join(SKILLS, "yt-qc", "qc.py"), "final.mp4", "--timeline", "timeline.json", "--profile", "long"]
    raise ValueError(f"no command for stage {sid}")


def make_tts_plan(slug):
    d = pdir(slug)
    text = spoken_text(os.path.join(d, "script.md"))
    v = _voice_module()
    chunks = v.split_chunks(text, LIMITS["tts_chunk_chars"])
    chars = sum(len(c) for c in chunks)
    collapsed = re.sub(r"\n[ \t]*\n+", "\n", text)
    plan = {"characters": chars, "chunks": len(chunks), "chunk_chars_max": max(len(c) for c in chunks),
            "chunk_limit": LIMITS["tts_chunk_chars"], "text_sha256": gates.sha256_text(text),
            "blank_line_chars": len(text) - len(collapsed), "cache_dir": "voice/cache",
            "voice": "Adam pNInz6obpgDQGcFmaJgB (channel default)", "cost_class": "paid - needs owner approval + --confirm",
            "credits_estimate": chars}
    _save(os.path.join(d, "voice", "tts_plan.json"), plan)
    return plan


def ledger_add(d, entry):
    p = os.path.join(d, "ledger.json")
    L = _load(p, {"entries": []})
    L["entries"].append(dict(entry, at=now()))
    _save(p, L)


def run(slug, stage_id=None, confirm=False, overwrite=False):
    d = pdir(slug)
    st = status(slug)
    row = next((r for r in st["stages"] if r["stage"] == stage_id), None) if stage_id else \
        next((r for r in st["stages"] if r["state"] not in ("done",)), None)
    if row is None: return {"ok": False, "error": f"unknown stage {stage_id}"}
    sid, s = row["stage"], STAGES[row["stage"]]
    if s["kind"] == "agent":
        return {"ok": False, "action_required": "agent", "stage": sid, "skill": s.get("skill"), "how": s.get("how"),
                "missing_outputs": row["missing_outputs"], "note": "creative stage - do it, then: orbital.py complete %s %s" % (slug, sid)}
    if row["state"] == "blocked":
        why = {n: next(r for r in st["stages"] if r["stage"] == n).get("gate", {}).get("problems") or "not produced yet" for n in row["blocked_by"]}
        return {"ok": False, "stage": sid, "blocked_by": row["blocked_by"], "why": why}
    state = _load(os.path.join(d, "state.json"), {"stages": {}})
    rec = state["stages"].setdefault(sid, {})
    approvals = _load(os.path.join(d, "approvals.json"), {})
    pitfalls = kb.for_stage(sid)                       # memory is consulted BEFORE the stage runs and recorded with the result
    rec["pitfalls_consulted"] = [p["id"] for p in pitfalls]
    result = {"stage": sid, "known_pitfalls": [{"id": p["id"], "fix": p["fix"]} for p in pitfalls]}
    if sid == "tts_plan":
        result.update(ok=True, plan=make_tts_plan(slug))
    elif sid == "tts":
        a = approvals.get("tts") or {}
        plan = _load(os.path.join(d, "voice", "tts_plan.json"), {})
        if not a.get("approved") or a.get("approved_by") != "user" or not a.get("quote"):
            return {"ok": False, "stage": sid, "error": "no owner approval for paid TTS in approvals.json (approve SLUG tts --max-chars N --quote ...). Nothing was sent."}
        if not confirm:
            return {"ok": False, "stage": sid, "error": "paid stage needs --confirm. Nothing was sent.", "plan": plan}
        if plan.get("characters", 10**9) > a.get("max_chars", 0):
            return {"ok": False, "stage": sid, "error": f"{plan.get('characters')} chars exceed the approved {a.get('max_chars')}. Nothing was sent."}
        if plan.get("text_sha256") != gates.sha256_text(spoken_text(os.path.join(d, "script.md"))):
            return {"ok": False, "stage": sid, "error": "script changed after the plan; re-run tts_plan and ask the owner again. Nothing was sent."}
        cmd = [sys.executable, os.path.join(SKILLS, "yt-voice", "voice.py"), "--script", "script.md", "--output", "voice/narration.wav",
               "--max-chars", str(a["max_chars"]), "--max-chunk-chars", str(LIMITS["tts_chunk_chars"]), "--context",
               "--cache-dir", "voice/cache", "--confirm"] + _auth_args() + (["--overwrite"] if overwrite else [])
        r = execute(cmd, d, retryable=False, allow_autofix=False)
        ledger_add(d, {"stage": "tts", "characters": plan.get("characters"), "ok": r["ok"], "approved_max": a["max_chars"]})
        if not r["ok"]:
            r["warning"] = ("A failed paid request may still have been billed. Do NOT rerun before checking the credits and voice/cache/ "
                            "(registry: tts-no-blind-retry). Copy voice/cache/ to the media/<slug>-audio branch.")
        result.update(r)
    else:
        if row["state"] == "needs_approval":
            return {"ok": False, "stage": sid, "error": "needs approval"}
        cmd = stage_command(sid, d, overwrite)
        r = execute(cmd, d, retryable=s.get("retryable", False))
        if sid == "qc":                                   # yt-qc exits 1 on FAIL but its JSON is the record
            os.makedirs(os.path.join(d, "qc"), exist_ok=True)
            out = r.get("stdout") or ""
            if out.strip():
                with open(os.path.join(d, "qc", "qc.json"), "w", encoding="utf-8") as f: f.write(out)
        result.update(r)
    if result.get("ok"):
        g = run_gate(s, d)
        result["gate"] = g
        if g["ok"]:
            rec.update(completed=now(), inputs_sha=_inputs_sha(s, d)); rec.pop("last_failure", None)
        else:
            result["ok"] = False
    if not result.get("ok"):
        rec["last_failure"] = {"at": now(), "attempts": len(result.get("attempts", [])), "diagnosis": [x["id"] for x in result.get("diagnosis", [])],
                               "gate_problems": (result.get("gate") or {}).get("problems")}
    result.pop("stdout", None)
    _save(os.path.join(d, "state.json"), state)
    return result


def complete(slug, sid):
    d = pdir(slug)
    s = STAGES.get(sid)
    if not s: raise ValueError(f"unknown stage {sid}")
    miss = [o for o in s["outputs"] if not os.path.exists(os.path.join(d, o))]
    if miss: return {"ok": False, "missing_outputs": miss}
    g = run_gate(s, d)
    if not g["ok"]: return {"ok": False, "gate": g}
    state = _load(os.path.join(d, "state.json"), {"stages": {}})
    state["stages"].setdefault(sid, {}).update(completed=now(), inputs_sha=_inputs_sha(s, d))
    _save(os.path.join(d, "state.json"), state)
    return {"ok": True, "stage": sid, "gate": g}


def init(slug):
    d = pdir(slug)
    if os.path.exists(d): return {"ok": False, "error": f"productions/{slug} already exists"}
    for sub in ("research", "story", "voice", "captions", "qc", "release", "assets"):
        os.makedirs(os.path.join(d, sub))
    _save(os.path.join(d, "state.json"), {"slug": slug, "created": now(), "stages": {}})
    _save(os.path.join(d, "approvals.json"), {"note": "Owner approvals for paid or irreversible actions. Written by Claude ONLY after the owner said yes in chat; quote their words.",
                                              "tts": {"approved": False}, "publish": {"approved": False, "note": "the agent never uploads"}})
    return {"ok": True, "created": f"productions/{slug}", "next": "orbital.py next " + slug}


def lock(slug):
    d = pdir(slug)
    text = spoken_text(os.path.join(d, "script.md"))
    _save(os.path.join(d, "story", "SCRIPT_LOCK.json"), {"spoken_sha256": gates.sha256_text(text), "characters": len(text), "locked_at": now(),
                                                         "rule": "changing the spoken text invalidates narration and costs a new paid TTS"})
    return {"ok": True, "characters": len(text)}


def approve(slug, what, max_chars, quote):
    if what != "tts": raise ValueError("only 'tts' can be approved here; publishing is never approved for the agent")
    if not quote or len(quote) < 3: raise ValueError("--quote with the owner's words is required")
    d = pdir(slug)
    a = _load(os.path.join(d, "approvals.json"), {})
    a["tts"] = {"approved": True, "approved_by": "user", "max_chars": int(max_chars), "quote": quote, "date": now()}
    _save(os.path.join(d, "approvals.json"), a)
    return {"ok": True, "tts": a["tts"]}


def preflight():
    checks = []
    def add(name, ok, detail=""): checks.append({"check": name, "ok": bool(ok), "detail": detail})
    for tool in ("ffmpeg", "ffprobe"): add(tool, shutil.which(tool), shutil.which(tool) or "not installed")
    for mod in ("PIL", "numpy"):
        try: __import__(mod); add("python:" + mod, True)
        except ImportError: add("python:" + mod, False, "pip install pillow numpy")
    add("elevenlabs credential", bool(os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("YT_VOICE_AUTH") == "proxy"),
        "env key or YT_VOICE_AUTH=proxy present (value never shown); the egress proxy may also inject it - check with a free GET /v1/voices/<id>")
    add("USGS credentials (only for new Landsat)", bool(os.environ.get("USGS_M2M_USERNAME") and os.environ.get("USGS_M2M_TOKEN")), "optional")
    br = subprocess.run(["git", "-C", ROOT, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
    add("not on main", br not in ("main", "master"), f"branch {br}")
    v = kb.validate()
    add("solutions registry valid", v["ok"], f"{v['entries']} entries, {len(v['problems'])} problems")
    st = os.path.join(ROOT, ".claude", "settings.json")
    add("guard hook configured", os.path.exists(st) and "guard.py" in _read(st), ".claude/settings.json")
    return {"ok": all(c["ok"] for c in checks if c["check"] not in ("USGS credentials (only for new Landsat)",)), "checks": checks}


def _opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return 0
    cmd = a[0]
    try:
        if cmd == "preflight": r = preflight()
        elif cmd == "init": r = init(a[1])
        elif cmd == "status": r = status(a[1])
        elif cmd == "next": r = status(a[1])["next"] or {"done": True}
        elif cmd == "run": r = run(a[1], _opt(a, "--stage"), "--confirm" in a, "--overwrite" in a)
        elif cmd == "complete": r = complete(a[1], a[2])
        elif cmd == "lock": r = lock(a[1])
        elif cmd == "approve": r = approve(a[1], a[2], _opt(a, "--max-chars", 0), _opt(a, "--quote"))
        elif cmd == "ledger": r = _load(os.path.join(pdir(a[1]), "ledger.json"), {"entries": []})
        else: r = {"ok": False, "error": f"unknown command {cmd}"}
    except (ValueError, IndexError, OSError) as x:
        print(json.dumps({"ok": False, "error": f"{type(x).__name__}: {x}"})); return 2
    print(json.dumps(r, indent=1, ensure_ascii=False))
    return 0 if r.get("ok", True) is not False else 1


if __name__ == "__main__":
    sys.exit(main())
