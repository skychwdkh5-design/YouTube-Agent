#!/usr/bin/env python3
"""yt-orchestrate: one command from topic to release package, resumable, with hard stops before anything paid.

    python3 .claude/skills/yt-orchestrate/orchestrate.py new   [--slug S]             # skeleton + first task packets
    python3 .claude/skills/yt-orchestrate/orchestrate.py run    --slug S [--until STAGE] [--dry-run]
    python3 .claude/skills/yt-orchestrate/orchestrate.py run    --slug S --stage STAGE [--force]
    python3 .claude/skills/yt-orchestrate/orchestrate.py status --slug S

Stage kinds: auto (runs code), agent (the AI agent writes an artifact from tasks/<stage>.md; the orchestrator validates it),
paid/heavy (voice, render: need a signed approval file AND --allow-paid / --allow-render; otherwise only a plan is made).
State: productions/<slug>/state.json (atomic writes; input and output sha256 per stage; crash-safe). Nothing publishes.
"""
import argparse, hashlib, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(SK, "..", ".."))
PY = sys.executable
STAGES = ["topic", "research", "facts", "evidence", "script", "visualplan", "visuals", "storyboard", "visualcheck", "voice", "voicecheck", "captions", "render", "qc", "release"]
DEPS = {"topic": [], "research": ["topic"], "facts": ["research"], "evidence": ["topic", "research"], "script": ["facts", "evidence"], "visualplan": ["script", "evidence"],
        "visuals": ["visualplan", "evidence"], "storyboard": ["script", "evidence", "visuals"], "visualcheck": ["storyboard"], "voice": ["script", "storyboard", "visualcheck"],
        "voicecheck": ["voice"], "captions": ["voicecheck"], "render": ["storyboard", "visuals", "voice", "voicecheck", "captions"], "qc": ["render"], "release": ["facts", "storyboard"]}
KIND = {"topic": "agent", "research": "agent", "script": "agent", "voice": "paid", "render": "heavy"}
# What a stage IS: FULLY_AUTOMATED runs without manual preparation; AGENT_REQUIRED needs Claude to do an intellectual task (a task packet is written);
# OWNER_REQUIRED needs the owner's approval. A stage can be FULLY_AUTOMATED by default and AGENT_REQUIRED only when it hits a judgement item.
NATURE = {"topic": "AGENT_REQUIRED", "research": "AGENT_REQUIRED", "facts": "FULLY_AUTOMATED", "evidence": "FULLY_AUTOMATED", "script": "AGENT_REQUIRED", "visualplan": "FULLY_AUTOMATED",
          "visuals": "FULLY_AUTOMATED", "storyboard": "FULLY_AUTOMATED", "visualcheck": "FULLY_AUTOMATED", "voice": "OWNER_REQUIRED", "voicecheck": "FULLY_AUTOMATED", "captions": "FULLY_AUTOMATED",
          "render": "OWNER_REQUIRED", "qc": "FULLY_AUTOMATED", "release": "FULLY_AUTOMATED"}
DONE, TERMINAL_BLOCK = "done", ("blocked", "failed", "needs_agent", "awaiting_approval", "waiting", "interrupted")


class Halt(Exception):
    def __init__(self, status, note, outputs=None, **extra):
        super().__init__(note)
        self.status, self.note, self.outputs, self.extra = status, note, outputs or [], extra


# ---- helpers ----------------------------------------------------------------------------------------------------------
def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def tool(args, cwd, timeout=1800):
    r = subprocess.run([PY] + args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        d = {"status": "error", "error": (r.stderr or r.stdout)[-400:]}
    return r.returncode, d


class Ep:
    def __init__(self, slug):
        self.slug = slug
        self.root = os.path.join(REPO, "productions", slug)
        self.state_path = os.path.join(self.root, "state.json")
        self.lock = os.path.join(self.root, ".lock")

    def p(self, *a):
        return os.path.join(self.root, *a)

    def episode(self):
        return json.load(open(self.p("episode.json"), encoding="utf-8"))

    def load(self):
        if os.path.exists(self.state_path):
            return json.load(open(self.state_path))
        return {"schema": "yt-orchestrate/1", "slug": self.slug, "created": now(), "stages": {}, "costs": [], "log": []}

    def save(self, st):
        st["updated"] = now()
        write_json(self.state_path, st)


def hashes(ep, paths):
    return {p: sha(ep.p(p)) for p in paths if os.path.exists(ep.p(p))}


def spoken_text(script):
    out = []
    for line in script.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "[", ">", "---", "<!--")):
            continue
        out.append(re.sub(r"\s+", " ", re.sub(r"\{[^}]*\}", "", s.replace("**", ""))).strip())
    return "\n\n".join(out) + "\n"


def packet(ep, stage, text):
    os.makedirs(ep.p("tasks"), exist_ok=True)
    open(ep.p("tasks", f"{stage}.md"), "w", encoding="utf-8").write(text)


# ---- stage runners: return (outputs, note) or raise Halt ----------------------------------------------------------------
def run_topic(ep, ctx):
    if os.path.exists(ep.p("topic", "approval.json")):
        a = json.load(open(ep.p("topic", "approval.json")))
        if not a.get("approved"):
            raise Halt("blocked", "topic/approval.json exists but approved is not true")
        write_json(ep.p("topic", "topic.json"), {"status": "ok", "chosen": a.get("title") or ep.slug, "source": "owner approval", "approval": a})
        return ["topic/topic.json"], "owner-approved topic"
    if os.path.exists(ep.p("topic", "candidates.json")):
        c, d = tool([os.path.join(SK, "yt-topic", "topic.py"), "score", "--candidates", "topic/candidates.json", "--out", "topic/topic.json", "--memo", "topic/topic.md"], ep.root)
        if c != 0:
            raise Halt("blocked", f"yt-topic: {d.get('status')} {d.get('excluded') or d.get('error')}")
        return ["topic/topic.json", "topic/topic.md"], f"chosen {d['chosen']}"
    packet(ep, "topic", "# Task: topic discovery\n\n1. Run `python3 .claude/skills/yt-topic/topic.py collect --queries \"q1;q2;...\" --out topic/videos_<name>.json` for 3-5 candidate topics (CLAUDE.md: unusual geography, satellite-visible change, strong US appeal).\n"
           "2. Run `topic.py imagery --aoi=minlon,minlat,maxlon,maxlat --years 2020,2022,2024,2026` for each (write `--aoi=...` with the equals sign: negative longitudes otherwise break argument parsing).\n3. Write `topic/candidates.json` (schema in .claude/skills/yt-topic/SKILL.md) with ratings 1-5 and a written rationale for each of us/se/no/dk/intl/visual/curiosity/evidence/monetization. Do not invent audience, CTR or retention data.\n"
           "4. Re-run the orchestrator. The owner may instead approve a topic by writing `topic/approval.json` {\"approved\": true, \"title\": ...}.\n")
    raise Halt("needs_agent", "write topic/candidates.json (see tasks/topic.md)")


RESEARCH_TASK = """# Task: research (AGENT_REQUIRED)

Topic: see topic/topic.json. Do the reading and searching with your own tools (WebSearch, WebFetch), prefer primary and scientific sources, and note every unreachable primary.
Log what you did so the work is auditable:
  python3 .claude/skills/yt-research/research.py --root productions/{slug} log --tool WebSearch --query "..." --status ok --note "..."
  python3 .claude/skills/yt-research/research.py --root productions/{slug} fetch <url>      # Python-side read; blocked/dns/timeout is logged, never replaced
Write `research/notes.json` (schema yt-research/1) - see .claude/skills/yt-research/SKILL.md:
  - "geo": {{"focus": [lon,lat], "segment": [lon,lat], "ndwi_bbox": [...], "stacks": [{{"name":"stack","aoi":[minlon,minlat,maxlon,maxlat],"years":[...],"pixel_m":10,"window":"MM-DD:MM-DD","cloud":3}}, {{"name":"wide","role":"wide",...}}]}}
    (the AOI and years are a research decision; check availability with `yt-topic imagery`)
  - "notes": one per claim: id C1.., kind, statement, short (<= 44 chars, drawn on screen), source {{outlet,url,date,access,kind}}, independent_outlets, or evidence+basis for observations.
Confidence is DERIVED from the sources (a primary read gives high; search summaries need >= 2 independent outlets; unreachable gives low). Do not try to raise it.
Then run the orchestrator again; `yt-research build` turns the notes into claims.json and a coverage report.
"""


def run_research(ep, ctx):
    if os.path.exists(ep.p("research", "notes.json")):
        c, d = tool([os.path.join(SK, "yt-research", "research.py"), "--root", ".", "build"], ep.root)
        if c != 0:
            raise Halt("blocked", f"yt-research: {d.get('error')}")
        note = f"{d['claims']} claims ({d['usable']} usable), factual capacity about {d['capacity_minutes']} min" + (" - INSUFFICIENT_FOR_6_MIN" if d["insufficient_for_6_min"] else "")
        return ["claims.json", "research/report.md"], note
    if os.path.exists(ep.p("claims.json")):
        return ["claims.json"], "claims.json provided manually (legacy path, no provenance derivation)"
    packet(ep, "research", RESEARCH_TASK.format(slug=ep.slug))
    raise Halt("needs_agent", "write research/notes.json (see tasks/research.md)")


def run_facts(ep, ctx):
    c, d = tool([os.path.join(SK, "yt-facts", "facts.py"), "--claims", "claims.json", "--defer-evidence", "--root", "."], ep.root)
    if c != 0:
        raise Halt("blocked", "claims registry: " + "; ".join(d.get("problems") or [d.get("error", "?")])[:400])
    return [], f"{d['claims']} claims, registry ok"


def _geo(ep):
    p = ep.p("research", "notes.json")
    if os.path.exists(p):
        return json.load(open(p)).get("geo") or {}
    return {"stacks": ep.episode().get("evidence", {}).get("stacks", [])}


def sentinel_stack_args(stk, out):
    """Western-hemisphere coordinates start with '-': they must be joined to the flag (--aoi=-115.8,...), or argparse reads them as an option."""
    return [os.path.join(SK, "yt-sentinel", "sentinel.py"), "stack", "--aoi=" + ",".join(map(str, stk["aoi"])), "--years", ",".join(map(str, stk["years"])),
            "--window", stk.get("window", "09-28:10-20"), "--cloud", str(stk.get("cloud", 3)), "--out", out, "--pixel-m", str(stk.get("pixel_m", 10)), "--confirm", "--overwrite"]


def run_evidence(ep, ctx):
    geo = _geo(ep)
    if not geo.get("stacks"):
        raise Halt("blocked", "no geo.stacks in research/notes.json (the AOI is a research decision)")
    outs = []
    for stk in geo["stacks"]:
        out = f"evidence/{stk['name']}"
        if os.path.exists(ep.p(out, "provenance.json")) and not ctx["force"]:
            outs += [f"{out}/provenance.json", f"{out}/grid.json"]; continue
        args = sentinel_stack_args(stk, out)
        c, d = tool(args, ep.root)
        if c != 0:
            raise Halt("blocked", f"yt-sentinel {stk['name']}: {d.get('status')} {d.get('error')} {d.get('missing', '')}")
        outs += [f"{out}/provenance.json", f"{out}/grid.json"]
    if geo.get("ndwi_bbox"):
        if not os.path.exists(ep.p("evidence", "ndwi.json")) or ctx["force"]:
            c, d = tool([os.path.join(SK, "yt-sentinel", "sentinel.py"), "ndwi-series", "--provenance", f"evidence/{geo['stacks'][0]['name']}/provenance.json",
                         "--bbox=" + ",".join(map(str, geo["ndwi_bbox"])), "--out", "evidence/ndwi.json"], ep.root)
            if c != 0:
                raise Halt("blocked", f"yt-sentinel ndwi-series: {d.get('error')}")
        outs.append("evidence/ndwi.json")
    return outs, f"{len(geo['stacks'])} stacks" + (" + NDWI series" if geo.get("ndwi_bbox") else "")


def run_script(ep, ctx):
    c, d = tool([os.path.join(SK, "yt-script-agent", "scriptagent.py"), "brief", "--root", "."], ep.root)
    if c != 0:
        raise Halt("blocked", f"yt-script-agent brief: {d.get('error')}")
    if not os.path.exists(ep.p("script.md")):
        raise Halt("needs_agent", f"write script.md from tasks/script.md (target {d['target_words'][0]}-{d['target_words'][1]} words; factual capacity about {d['capacity_words']} words)", ["research/brief.json"])
    c, v = tool([os.path.join(SK, "yt-script-agent", "scriptagent.py"), "validate", "--root", "."], ep.root)
    if c != 0:
        raise Halt("blocked", "script: " + "; ".join(v.get("problems") or [v.get("error", "?")])[:600], ["research/brief.json"])
    return ["script.md", "research/brief.json"], f"{v['words']} words = {v['minutes']} min, {len(v['claims_used'])} claims used" + ("; " + "; ".join(v["warnings"]) if v.get("warnings") else "")


def run_visualplan(ep, ctx):
    if os.path.exists(ep.p("episode.json")):
        try:
            if json.load(open(ep.p("episode.json"))).get("generated_by") != "yt-visual-planner":
                return ["episode.json", "graphics_spec.json"], "hand-written episode.json kept (not generated by the planner)"
        except ValueError:
            pass
    c, d = tool([os.path.join(SK, "yt-visual-planner", "planner.py"), "--root", "."], ep.root)
    if c != 0:
        raise Halt("blocked", f"yt-visual-planner: {d.get('error')}")
    return ["episode.json", "graphics_spec.json"], f"{d['visuals']} visuals in {d['chapters']} chapters, graphics {d['graphics']}"


def run_visualcheck(ep, ctx):
    c, d = tool([os.path.join(SK, "yt-visualcheck", "visualcheck.py"), "--root", "."], ep.root)
    outs = ["qa/visual_claims.json", "qa/visual_claims.md"]
    if d.get("status") == "FAIL":
        raise Halt("blocked", f"visual-claim check FAIL {d.get('counts')} (see qa/visual_claims.md)", outs)
    if d.get("status") == "NEEDS_VISUAL_REVIEW":
        items = [i for i in json.load(open(ep.p("qa", "visual_claims.json")))["items"] if i["status"] == "NEEDS_VISUAL_REVIEW"]
        packet(ep, "visualcheck", "# Task: visual review (AGENT_REQUIRED)\n\nLook at each frame file, decide whether it supports the on-screen text, and record what you SAW:\n"
               f"  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/{ep.slug} review --item \"<item id>\" --verdict supports|does_not_support|unclear --note \"what the frame shows\"\n\n"
               + "\n".join(f"- `{i['id']}` claims {i['claims']}: text {i.get('text')!r}; frames " + ", ".join(f"[{k}] `{f['file']}`" + ("" if not f.get("review") else f" (reviewed: {f['review']})") for k, f in enumerate(i.get("frames") or [])) for i in items) + "\n\nA review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.\n")
        raise Halt("needs_agent", f"{len(items)} items NEEDS_VISUAL_REVIEW (see tasks/visualcheck.md)", outs)
    if c != 0:
        raise Halt("blocked", f"visualcheck: {d.get('error') or d}", outs)
    return outs, f"visual claims OK {d['counts']} of {d['total']} items" + (f"; {d['orphan_reviews']} orphan reviews (run `visualcheck.py prune`)" if d.get("orphan_reviews") else "")


def run_storyboard(ep, ctx):
    args = [os.path.join(SK, "yt-storyboard", "storyboard.py"), "--episode", "."]
    vm = ep.p("voice", "narration.voice.json")
    if os.path.exists(vm):
        args += ["--voice-meta", "voice/narration.voice.json"]
        if os.path.exists(ep.p("captions", "captions.srt")):
            args += ["--captions", "captions/captions.srt"]
    c, d = tool(args, ep.root)
    if c != 0:
        raise Halt("blocked", f"yt-storyboard: {d.get('error') or d.get('renderer')}")
    c2, d2 = tool([os.path.join(SK, "yt-facts", "facts.py"), "--claims", "claims.json", "--labels", "story/labels.json", "--root", "."], ep.root)
    if c2 != 0:
        raise Halt("blocked", "on-screen text vs claims: " + "; ".join(d2.get("problems") or [])[:400])
    return ["story/storyboard.json", "timeline.json", "story/labels.json", "story/report.md"], f"{d['shots']} shots, {d['duration']}s, timing from {d['timing']}"


def run_visuals(ep, ctx):
    e = ep.episode()
    spec = e.get("graphics")
    if not spec:
        return [], "no graphics requested"
    os.makedirs(ep.p("graphics"), exist_ok=True)
    c, d = tool([os.path.join(SK, "yt-graphics", "graphics.py"), spec, "--out-dir", "graphics"], ep.root)
    if c != 0:
        raise Halt("blocked", f"yt-graphics: {d.get('status')} {d.get('error')}")
    outs = sorted(f"graphics/{f}" for f in os.listdir(ep.p("graphics")) if f.endswith(".png"))
    return outs, f"{len(outs)} graphics"


def _approval(ep, name, script_sha):
    p = ep.p("approvals", f"{name}.json")
    if not os.path.exists(p):
        return None, f"no approvals/{name}.json"
    a = json.load(open(p))
    if not a.get("approved"):
        return None, f"approvals/{name}.json: approved is not true"
    if a.get("script_sha256") != script_sha:
        return None, f"approvals/{name}.json was given for a different script (hash mismatch); ask the owner again"
    return a, ""


def owner_read(script_text, spoken, script_hash):
    """The narration as the owner reads it: chapters and numbered lines, no claim tags. Exactly the text that will be sent (checked below)."""
    out = ["# Narration text - exactly what will be sent to the voice provider", "",
           f"Words: {len(spoken.split())} | script sha256: `{script_hash}`", "", "Chapter titles and claim tags are not spoken.", ""]
    lines, n = [], 0
    for sec in re.split(r"^## ", script_text, flags=re.M)[1:]:
        head, _, body = sec.partition("\n")
        out.append("## " + (head.split(":", 1)[1].strip() if ":" in head else head))
        for ln in body.splitlines():
            t = re.sub(r"\s*\{[^}]*\}", "", ln).strip()
            if t:
                n += 1; out.append(f"{n}. {t}"); lines.append(t)
        out.append("")
    if re.sub(r"\s+", " ", " ".join(lines)).strip() != re.sub(r"\s+", " ", spoken).strip():
        raise Halt("blocked", "owner reading copy differs from the spoken text")
    return "\n".join(out)


def run_voice(ep, ctx):
    script = ep.p("script.md")
    os.makedirs(ep.p("voice"), exist_ok=True)
    open(ep.p("voice", "spoken.md"), "w", encoding="utf-8").write(spoken_text(open(script, encoding="utf-8").read()))
    open(ep.p("voice", "OWNER_READ.md"), "w", encoding="utf-8").write(owner_read(open(script, encoding="utf-8").read(), open(ep.p("voice", "spoken.md"), encoding="utf-8").read(), sha(script)))
    # the authoritative, billed character count is yt-voice's own plan (no --confirm: nothing is sent)
    pc, pd = tool([os.path.join(SK, "yt-voice", "voice.py"), "--script", "voice/spoken.md", "--output", "voice/narration.wav", "--auth", "proxy", "--max-chars", "1000000"], ep.root)
    chars = pd.get("characters") if pd.get("status") == "confirm_required" else len(open(ep.p("voice", "spoken.md"), encoding="utf-8").read())
    if os.path.exists(ep.p("voice", "narration.voice.json")) and os.path.exists(ep.p("voice", "narration.wav")):
        return ["voice/narration.wav", "voice/narration.voice.json"], "narration already generated (not regenerated)"
    model = pd.get("model_id", "unknown")
    per_char = {"eleven_multilingual_v2": 1.0, "eleven_turbo_v2_5": 0.5, "eleven_flash_v2_5": 0.5}.get(model)
    plan = {"chars": chars, "chunks": pd.get("chunks"), "script_sha256": sha(script), "spoken_sha256": sha(ep.p("voice", "spoken.md")), "provider": "elevenlabs", "model_id": model,
            "voice": f"{pd.get('voice_name', 'Adam')} ({pd.get('voice_id', 'pNInz6obpgDQGcFmaJgB')})",
            "max_credits": (chars * per_char) if per_char is not None else None,
            "credit_basis": ("published rate for " + model + f": {per_char} credit per character (one generation; account balance and plan could not be read: the API key lacks user_read)") if per_char is not None else "unknown model: cost not computed",
            "command_after_owner_approval": f"python3 .claude/skills/yt-orchestrate/orchestrate.py run --slug {ep.slug} --stage voice --allow-paid",
            "note": "PAID. Owner must set approvals/voice.json approved:true (script_sha256, max_chars >= chars, a fresh approval_id) and run with --allow-paid. One approval_id = one attempt, success or failure."}
    write_json(ep.p("voice", "plan.json"), plan)
    a, why = _approval(ep, "voice", plan["script_sha256"])
    if not a or not ctx["allow_paid"]:
        raise Halt("awaiting_approval", (why or "approval present but --allow-paid not given") + f"; plan: {chars} characters", ["voice/plan.json"])
    if ctx["dry"]:
        raise Halt("awaiting_approval", "dry-run: paid call not made", ["voice/plan.json"])
    if a.get("max_chars", 0) < chars:
        raise Halt("blocked", f"approved max_chars {a.get('max_chars')} < {chars} characters")
    # ONE approval buys ONE paid attempt. The attempt is written to a ledger BEFORE the call, so a network error, a crash or a rerun can never spend again on the same approval.
    aid = str(a.get("approval_id") or "").strip()
    if not aid:
        raise Halt("blocked", "approvals/voice.json needs a non-empty approval_id (a new one for every paid attempt)")
    ledger_p = ep.p("voice", "spend_ledger.json")
    ledger = json.load(open(ledger_p)) if os.path.exists(ledger_p) else []
    used = [e for e in ledger if e.get("approval_id") == aid]
    if used:
        raise Halt("blocked", f"approval_id {aid!r} was already used (status {used[-1].get('status')}); credits may have been spent. The owner must inspect the ElevenLabs usage and issue a NEW approval_id for another attempt")
    entry = {"approval_id": aid, "script_sha256": plan["script_sha256"], "chars": chars, "max_chars": a["max_chars"], "model_id": model, "started": now(), "status": "started"}
    ledger.append(entry)
    write_json(ledger_p, ledger)
    voice_tool = os.environ.get("OA_VOICE_TOOL") or os.path.join(SK, "yt-voice", "voice.py")   # OA_VOICE_TOOL: test seam only, never set in production
    c, d = tool([voice_tool, "--script", "voice/spoken.md", "--output", "voice/narration.wav", "--auth", "proxy", "--confirm", "--max-chars", str(a["max_chars"])], ep.root)
    if c != 0:
        entry.update(status="failed", finished=now(), error=f"{d.get('status')}: {d.get('error')}", note="a request may have been billed before the failure")
        write_json(ledger_p, ledger)
        raise Halt("failed", f"yt-voice: {d.get('status')} {d.get('error')}; approval {aid!r} is now spent, no automatic retry")
    entry.update(status="ok", finished=now())
    write_json(ledger_p, ledger)
    ctx["costs"].append({"stage": "voice", "chars": chars, "provider": "elevenlabs", "at": now(), "note": "approved by owner"})
    return ["voice/narration.wav", "voice/narration.voice.json"], f"generated {chars} chars"


def run_voicecheck(ep, ctx):
    """Free check of the real narration; FAIL blocks captions/render. Pronunciation needs a human ear: the result is NEEDS_HUMAN_LISTEN, never PASS."""
    c, d = tool([os.path.join(SK, "yt-voicecheck", "voicecheck.py"), "--root", "."], ep.root)
    if d.get("result") == "FAIL":
        raise Halt("blocked", "voicecheck FAIL: " + "; ".join(f"{x['id']}: {x['detail']}" for x in d.get("checks", []) if x["status"] == "fail")[:400], ["voice/voicecheck.json"])
    return ["voice/voicecheck.json"], f"{d.get('result')}: {len(d.get('risky', []))} risky words to listen to; storyboard re-timed from real word timings"


def run_captions(ep, ctx):
    os.makedirs(ep.p("captions"), exist_ok=True)
    c, d = tool([os.path.join(SK, "yt-captions", "captions.py"), "--voice", "voice/narration.voice.json", "--out-dir", "captions", "--overwrite"], ep.root)
    if c != 0:
        raise Halt("blocked", f"yt-captions: {d.get('error') or d.get('status')}")
    return ["captions/captions.srt", "captions/captions.vtt", "captions/captions.json"], "captions built from real word timings"


def run_render(ep, ctx):
    os.makedirs(ep.p("render"), exist_ok=True)
    plan_c, plan = tool([os.path.join(SK, "yt-render", "render.py"), "--timeline", "timeline.json"], ep.root)
    write_json(ep.p("render", "plan.json"), plan)
    if plan.get("status") not in ("confirm_required", "ok"):
        raise Halt("blocked", f"render plan: {plan.get('error')}", ["render/plan.json"])
    a, why = _approval(ep, "render", sha(ep.p("script.md")))
    if not a or not ctx["allow_render"]:
        raise Halt("awaiting_approval", (why or "approval present but --allow-render not given") + "; plan validated", ["render/plan.json"])
    if ctx["dry"]:
        raise Halt("awaiting_approval", "dry-run: render not started", ["render/plan.json"])
    c, d = tool([os.path.join(SK, "yt-render", "render.py"), "--timeline", "timeline.json", "--output", "render/final.mp4", "--confirm", "--overwrite"], ep.root, 3600)
    if c != 0:
        raise Halt("failed", f"yt-render: {d.get('error')}")
    return ["render/final.mp4", "render/final.manifest.json"], "rendered"


def _srt_cues(text):
    out = []
    for blk in re.split(r"\n\s*\n", text.strip()):
        ln = blk.splitlines()
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+) --> (\d+):(\d+):(\d+)[,.](\d+)", blk)
        if m:
            g = list(map(int, m.groups()))
            out.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, blk))
    return out


def render_test(slug, seconds=30.0, run_it=False):
    """Short render of the first N seconds on the real timeline, the real narration (trimmed copy) and real captions. Never the full video."""
    ep = Ep(slug)
    need = ["timeline.json", "voice/narration.wav", "voice/narration.voice.json", "captions/captions.srt"]
    miss = [f for f in need if not os.path.exists(ep.p(f))]
    if miss:
        return {"status": "blocked", "error": f"cannot build the test: missing {miss}; the narration does not exist yet (voice is not approved/generated)"}, 1
    vc = json.load(open(ep.p("voice", "voicecheck.json"))) if os.path.exists(ep.p("voice", "voicecheck.json")) else {}
    if vc.get("result") == "FAIL":
        return {"status": "blocked", "error": "voicecheck FAIL: fix the narration before any render"}, 1
    tl = json.load(open(ep.p("timeline.json")))
    meta = json.load(open(ep.p("voice", "narration.voice.json")))
    allcues = _srt_cues(open(ep.p("captions", "captions.srt"), encoding="utf-8").read())
    # cut at the end of the first caption cue that reaches the requested length: never mid-sentence, never a stretch without subtitles
    last = next((c for c in allcues if c[1] >= seconds), allcues[-1] if allcues else None)
    if last is None:
        return {"status": "blocked", "error": "captions.srt has no cues"}, 1
    words = [w for w in meta["words"] if w["end"] <= last[1] + 0.05]
    if not words:
        return {"status": "blocked", "error": "no word ends within the test window"}, 1
    t_end = round(last[1] + 0.4, 3)
    d = ep.p("render", "test")
    os.makedirs(d, exist_ok=True)
    wav = os.path.join(d, "narration.test.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", ep.p("voice", "narration.wav"), "-t", f"{t_end:.3f}", wav], check=True)
    m2 = dict(meta, words=words, audio="narration.test.wav", audio_sha256=sha(wav), duration=probe_duration(wav), characters=sum(len(w["text"]) for w in words),
              text=" ".join(w["text"] for w in words), text_sha256=hashlib.sha256(" ".join(w["text"] for w in words).encode()).hexdigest(), test_excerpt=True)
    write_json(os.path.join(d, "narration.test.voice.json"), m2)
    cues = [c for c in allcues if c[1] <= last[1] + 0.05]
    open(os.path.join(d, "captions.test.srt"), "w", encoding="utf-8").write("\n\n".join(f"{i}\n" + "\n".join(b.splitlines()[1:]) for i, (_, _, b) in enumerate(cues, 1)) + "\n")
    t = dict(tl, shots=[x for x in tl["shots"] if x["start"] < t_end], end={"seconds": max(1, round(m2["duration"] + 0.5, 2))})
    t["voice"] = {"src": "render/test/narration.test.wav", "meta": "render/test/narration.test.voice.json"}
    t["captions"] = {"src": "render/test/captions.test.srt", "preset": "default"}
    write_json(os.path.join(d, "timeline.test.json"), t)
    base = [os.path.join(SK, "yt-render", "render.py"), "--timeline", "render/test/timeline.test.json", "--media-root", "."]
    c, plan = tool(base, ep.root)
    res = {"status": plan.get("status"), "seconds": round(m2["duration"], 2), "shots": len(t["shots"]), "plan_error": plan.get("error"), "warnings": plan.get("warnings") or (plan.get("plan") or {}).get("warnings")}
    if not run_it:
        res["next"] = f"python3 .claude/skills/yt-orchestrate/orchestrate.py render-test --slug {slug} --seconds {seconds:g} --run"
        return res, 0 if plan.get("status") in ("confirm_required", "ok") else 1
    c, out = tool(base + ["--output", "render/test/test.mp4", "--confirm", "--overwrite"], ep.root, 900)
    res.update(status=out.get("status"), output="render/test/test.mp4", error=out.get("error"))
    return res, 0 if c == 0 else 1


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return round(float(r.stdout.strip()), 3)


def run_qc(ep, ctx):
    c, d = tool([os.path.join(SK, "yt-qc", "qc.py"), "render/final.mp4", "--timeline", "timeline.json", "--profile", "long"], ep.root)
    write_json(ep.p("render", "qc.json"), d)
    if d.get("result") != "PASS":
        fails = [x["id"] for x in d.get("checks", []) if x.get("status") == "fail"]
        raise Halt("blocked", f"qc {d.get('result')}: {fails}", ["render/qc.json"])
    return ["render/qc.json"], "QC PASS"


def run_release(ep, ctx):
    e = ep.episode() if os.path.exists(ep.p('episode.json')) else {}
    st_full = ctx["state"]
    st = ctx["state"]["stages"]
    pending = [s for s in STAGES if s != "release" and st.get(s, {}).get("status") != DONE]
    claims = json.load(open(ep.p("claims.json")))["claims"]
    L = [f"# Release package - {e.get('title', ep.slug)}", "", f"Generated {now()}. Nothing is published.", "",
         "## Status", *[f"- {s}: {st.get(s, {}).get('status', 'pending')} {st.get(s, {}).get('note', '')}" for s in STAGES if s != "release"], "",
         "## Autonomy (what was automated)", *[f"- {r['stage']}: {r['nature']} / now {r['class_now']} / {r['produced_by']}" for r in autonomy(st_full)["stages"]], "",
         "## Title options (working title approved by owner; not final)", *[f"- {t}" for t in e.get("titles", [])], "",
         "## Claims ledger", *[f"- {c['id']} [{c['tier']}/{c['confidence']}] {c['text']}" + (f" ({c.get('attribution')}, {c.get('date')}, {c.get('url')})" if c.get("url") else "") for c in claims], "",
         "## Costs", *([f"- {c}" for c in ctx["state"]["costs"]] or ["- none (no paid action taken)"]), ""]
    if pending:
        L += ["## Package is INCOMPLETE", "Pending: " + ", ".join(pending), "", "**Owner question: approve the paid step(s) listed as awaiting_approval, or change?**"]
    else:
        L += ["## Ready for review", "**Owner question: approve for publishing, or change?** (publishing is never automatic)"]
    os.makedirs(ep.p("release"), exist_ok=True)
    open(ep.p("release", "REVIEW.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    outs = ["release/REVIEW.md"]
    for f in ("story/report.md",):
        if os.path.exists(ep.p(f)):
            outs.append(f)
    return outs, "incomplete" if pending else "complete"


RUN = {"topic": run_topic, "research": run_research, "facts": run_facts, "evidence": run_evidence, "script": run_script, "visualplan": run_visualplan, "visualcheck": run_visualcheck, "storyboard": run_storyboard,
       "visuals": run_visuals, "voice": run_voice, "voicecheck": run_voicecheck, "captions": run_captions, "render": run_render, "qc": run_qc, "release": run_release}
# files whose change invalidates a stage (besides the outputs of its dependencies)
INPUTS = {"topic": ["topic/approval.json", "topic/candidates.json"], "research": ["research/notes.json"], "facts": ["claims.json"], "evidence": ["research/notes.json"],
          "script": ["script.md", "claims.json", "evidence/stack/provenance.json"], "visualplan": ["script.md", "claims.json", "research/notes.json", "evidence/stack/provenance.json"],
          "visuals": ["episode.json", "graphics_spec.json", "evidence/stack/provenance.json"],
          "storyboard": ["script.md", "episode.json", "claims.json", "evidence/stack/grid.json", "voice/narration.voice.json", "captions/captions.srt"],
          "visualcheck": ["story/storyboard.json", "story/labels.json", "qa/visual_review.json", "evidence/ndwi.json", "claims.json", "episode.json", "graphics_spec.json",
                         "evidence/stack/provenance.json", "evidence/stack/grid.json"],     # provenance carries the sha256 of every stack image the frames are cropped from
          "voice": ["script.md", "approvals/voice.json"], "voicecheck": ["voice/narration.voice.json", "voice/spoken.md"], "captions": ["voice/narration.voice.json", "voice/voicecheck.json"], "render": ["timeline.json", "approvals/render.json"],
          "qc": ["render/final.mp4", "timeline.json"], "release": ["claims.json", "story/report.md", "qa/visual_claims.json"]}
# files an agent wrote for a stage (recorded in state.json so the autonomy report can tell agent work from code work)
AGENT_ARTIFACTS = {"topic": ["topic/approval.json", "topic/candidates.json"], "research": ["research/notes.json", "claims.json"], "script": ["script.md"], "visualcheck": ["qa/visual_review.json"]}

TOOLS = {"topic": ["yt-topic/topic.py"], "research": ["yt-research/research.py"], "facts": ["yt-facts/facts.py"], "evidence": ["yt-sentinel/sentinel.py"], "visuals": ["yt-graphics/graphics.py", "yt-geo/geostack.py"],
         "script": ["yt-facts/facts.py", "yt-script-agent/scriptagent.py"], "visualplan": ["yt-visual-planner/planner.py"], "visualcheck": ["yt-visualcheck/visualcheck.py", "yt-geo/geostack.py"],
         "storyboard": ["yt-storyboard/storyboard.py", "yt-facts/facts.py"], "voicecheck": ["yt-voicecheck/voicecheck.py"], "captions": ["yt-captions/captions.py"], "render": ["yt-render/render.py", "yt-render/compose.py"], "qc": ["yt-qc/qc.py"]}


def tool_hash(stage):
    h = hashlib.sha256()
    for f in TOOLS.get(stage, []):
        p = os.path.join(SK, f)
        if os.path.exists(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:16]


def ordered_inputs(ep, stage, st):
    files = list(INPUTS.get(stage, []))
    for d in DEPS[stage]:
        files += st["stages"].get(d, {}).get("outputs", {}).keys()
    return sorted(set(files))


def run(slug, until=None, only=None, force=False, dry=False, allow_paid=False, allow_render=False):
    ep = Ep(slug)
    if not os.path.isdir(ep.root):
        return {"status": "error", "error": f"productions/{slug} does not exist; run `new --slug {slug}`"}, 1
    os.makedirs(ep.root, exist_ok=True)
    if os.path.exists(ep.lock):
        try:
            pid = int(open(ep.lock).read().strip() or 0)
            os.kill(pid, 0)
            return {"status": "locked", "error": f"another run (pid {pid}) is active"}, 1
        except (ValueError, ProcessLookupError, PermissionError):
            pass
    open(ep.lock, "w").write(str(os.getpid()))
    st = ep.load()
    ctx = {"force": force, "dry": dry, "allow_paid": allow_paid, "allow_render": allow_render, "costs": st["costs"], "state": st}
    report, virtual = {}, set()
    try:
        for pass_no in range(3):      # a later stage (voice, captions) can invalidate an earlier one (storyboard): run again, bounded
            ran = False
            for stage in STAGES:
                rec = st["stages"].setdefault(stage, {"status": "pending", "attempts": 0})
                if rec["status"] == "running":
                    rec["status"] = "interrupted"
                    st["log"].append({"at": now(), "stage": stage, "event": "found interrupted from an earlier run; will rerun"})
                if only and stage != only:
                    report[stage] = rec["status"]; continue
                if until and STAGES.index(stage) > STAGES.index(until):
                    break
                blockers = [d for d in DEPS[stage] if st["stages"].get(d, {}).get("status") != DONE and d not in virtual]
                if blockers:
                    if not dry:
                        if rec["status"] == DONE:      # an upstream stage is no longer done: this result is stale and must not be trusted
                            st["log"].append({"at": now(), "stage": stage, "event": f"invalidated: upstream {blockers} not done"})
                        rec["status"], rec["note"] = "waiting", f"waiting for {blockers}"
                    report[stage] = rec["status"]; continue
                ins = hashes(ep, ordered_inputs(ep, stage, st))
                ins["_tool"] = tool_hash(stage)     # a changed tool re-runs its stage
                cached = (stage != "release" and rec["status"] == DONE and not (force and (not only or stage == only)) and rec.get("inputs") == ins
                          and all(os.path.exists(ep.p(o)) and sha(ep.p(o)) == h for o, h in rec.get("outputs", {}).items()))
                if cached:
                    report.setdefault(stage, "cached"); continue
                if rec["status"] == DONE:
                    st["log"].append({"at": now(), "stage": stage, "event": "inputs or outputs changed; rerun"})
                if dry:
                    report[stage] = "would_run"; virtual.add(stage); continue
                rec.update(status="running", started=now(), attempts=rec.get("attempts", 0) + 1, error=None)
                ep.save(st)
                if os.environ.get("OA_CRASH_IN") == stage:
                    os._exit(99)                       # test hook: simulated hard crash while running
                try:
                    outs, note = RUN[stage](ep, ctx)
                    rec.update(status=DONE, finished=now(), note=note, inputs=ins, outputs=hashes(ep, outs), error=None, agent_artifacts=hashes(ep, AGENT_ARTIFACTS.get(stage, [])))
                    ran = ran or stage != "release"
                    st["log"].append({"at": now(), "stage": stage, "event": "done", "note": note})
                except Halt as h:
                    rec.update(status=h.status, finished=now(), note=h.note, error=h.note if h.status in ("blocked", "failed") else None, outputs=hashes(ep, h.outputs))
                    st["log"].append({"at": now(), "stage": stage, "event": h.status, "note": h.note})
                except Exception as e:             # a bug or an environment failure is a blocked stage, never a traceback
                    rec.update(status="failed", finished=now(), error=f"{type(e).__name__}: {e}")
                    st["log"].append({"at": now(), "stage": stage, "event": "failed", "note": rec["error"]})
                report[stage] = rec["status"] if rec["status"] != "cached" else report.get(stage, "cached")
                ep.save(st)
                if os.environ.get("OA_STOP_AFTER") == stage:
                    break
            ctx["force"] = False; force = False          # --force applies to the first pass only
            if dry or not ran:
                break
        if not dry:
            ep.save(st)
    finally:
        try:
            os.remove(ep.lock)
        except OSError:
            pass
    nxt = next((s for s in STAGES if st["stages"].get(s, {}).get("status") not in (DONE, None)), None)
    res = {"status": "ok" if all(st["stages"].get(s, {}).get("status") == DONE for s in STAGES) else "incomplete", "slug": slug, "stages": report,
           "next": {nxt: st["stages"][nxt].get("note")} if nxt else None, "autonomy": {k: v for k, v in autonomy(st).items() if k != "stages"}, "dry_run": dry}
    return res, 0


def autonomy(st):
    """What was actually automated: per stage nature, current state, and whether an agent artifact was involved."""
    rows, auto_done, agent_done, owner_pending, need_agent = [], 0, 0, 0, 0
    for s in STAGES:
        r = st["stages"].get(s, {})
        status = r.get("status", "pending")
        now_cls = "AGENT_REQUIRED" if status == "needs_agent" else "OWNER_REQUIRED" if status == "awaiting_approval" else NATURE[s]
        by = ("agent artifact, then code" if r.get("agent_artifacts") else "code") if status == DONE else "-"
        if status == DONE and NATURE[s] == "FULLY_AUTOMATED" and not r.get("agent_artifacts"):
            auto_done += 1
        elif status == DONE:
            agent_done += 1
        if status == "awaiting_approval" or (status in ("waiting", "pending") and NATURE[s] == "OWNER_REQUIRED"):
            owner_pending += 1
        if status == "needs_agent":
            need_agent += 1
        rows.append({"stage": s, "nature": NATURE[s], "status": status, "class_now": now_cls, "produced_by": by})
    return {"stages": rows, "fully_automated_done": auto_done, "agent_work_done": agent_done, "agent_needed_now": need_agent, "owner_gates_pending": owner_pending, "total": len(STAGES)}


def status(slug):
    ep = Ep(slug)
    st = ep.load()
    return {"slug": slug, "stages": {s: {"status": st["stages"].get(s, {}).get("status", "pending"), "note": st["stages"].get(s, {}).get("note")} for s in STAGES},
            "autonomy": autonomy(st), "costs": st["costs"], "updated": st.get("updated")}, 0


def new(slug):
    slug = slug or "ep-" + time.strftime("%Y%m%d")
    ep = Ep(slug)
    os.makedirs(ep.p("topic"), exist_ok=True)
    return {"status": "ok", "slug": slug, "next": f"python3 .claude/skills/yt-orchestrate/orchestrate.py run --slug {slug}"}, 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("--slug")
    r = sub.add_parser("run"); r.add_argument("--slug", required=True); r.add_argument("--until", choices=STAGES); r.add_argument("--stage", choices=STAGES)
    r.add_argument("--force", action="store_true"); r.add_argument("--dry-run", action="store_true")
    r.add_argument("--allow-paid", action="store_true", help="permit yt-voice if approvals/voice.json matches the script")
    r.add_argument("--allow-render", action="store_true", help="permit the full render if approvals/render.json matches")
    t = sub.add_parser("render-test"); t.add_argument("--slug", required=True); t.add_argument("--seconds", type=float, default=30.0); t.add_argument("--run", action="store_true")
    s = sub.add_parser("status"); s.add_argument("--slug", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "new":
        res, code = new(a.slug)
    elif a.cmd == "render-test":
        res, code = render_test(a.slug, a.seconds, a.run)
    elif a.cmd == "status":
        res, code = status(a.slug)
    else:
        res, code = run(a.slug, a.until, a.stage, a.force, a.dry_run, a.allow_paid, a.allow_render)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
