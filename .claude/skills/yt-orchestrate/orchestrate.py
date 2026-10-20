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
STAGES = ["topic", "research", "facts", "evidence", "visuals", "script", "storyboard", "voice", "captions", "render", "qc", "release"]
DEPS = {"topic": [], "research": ["topic"], "facts": ["research"], "evidence": ["topic"], "script": ["facts", "evidence"],
        "storyboard": ["script", "evidence", "visuals"], "visuals": ["evidence"], "voice": ["script", "storyboard"],
        "captions": ["voice"], "render": ["storyboard", "visuals", "voice", "captions"], "qc": ["render"], "release": ["facts", "storyboard"]}
KIND = {"topic": "agent", "research": "agent", "script": "agent", "voice": "paid", "render": "heavy"}
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
           "2. Run `topic.py imagery --aoi minlon,minlat,maxlon,maxlat --years 2020,2022,2024,2026` for each.\n3. Write `topic/candidates.json` (schema in .claude/skills/yt-topic/SKILL.md) with ratings 1-5 and a written rationale for each of us/se/no/dk/intl/visual/curiosity/evidence/monetization. Do not invent audience, CTR or retention data.\n"
           "4. Re-run the orchestrator. The owner may instead approve a topic by writing `topic/approval.json` {\"approved\": true, \"title\": ...}.\n")
    raise Halt("needs_agent", "write topic/candidates.json (see tasks/topic.md)")


def run_research(ep, ctx):
    if not os.path.exists(ep.p("claims.json")):
        packet(ep, "research", "# Task: research and claims\n\nCollect sources for the topic (primary first; say when a primary is unreachable). Write `claims.json` (schema yt-facts/1, see .claude/skills/yt-facts/SKILL.md): "
               "every claim has a tier (original/media/org/science/observation/hypothesis), confidence, and for media/org/science an attribution, date, URL and the wording word ('reported'/'said'). "
               "Observations point to an evidence file. Never raise confidence to make a script fit.\n")
        raise Halt("needs_agent", "write claims.json (see tasks/research.md)")
    return ["claims.json"], "claims.json present"


def run_facts(ep, ctx):
    c, d = tool([os.path.join(SK, "yt-facts", "facts.py"), "--claims", "claims.json", "--defer-evidence", "--root", "."], ep.root)
    if c != 0:
        raise Halt("blocked", "claims registry: " + "; ".join(d.get("problems") or [d.get("error", "?")])[:400])
    return [], f"{d['claims']} claims, registry ok"


def run_evidence(ep, ctx):
    cfg = ep.episode().get("evidence", {})
    outs = []
    for stk in cfg.get("stacks", []):
        out = f"evidence/{stk['name']}"
        if os.path.exists(ep.p(out, "provenance.json")) and not ctx["force"]:
            outs.append(f"{out}/provenance.json"); continue
        if ctx["dry"]:
            raise Halt("waiting", f"dry-run: would build stack {stk['name']} (free, Sentinel-2)")
        args = [os.path.join(SK, "yt-sentinel", "sentinel.py"), "stack", "--aoi", ",".join(map(str, stk["aoi"])), "--years", ",".join(map(str, stk["years"])),
                "--window", stk.get("window", "09-28:10-20"), "--cloud", str(stk.get("cloud", 3)), "--out", out, "--pixel-m", str(stk.get("pixel_m", 10)), "--confirm", "--overwrite"]
        c, d = tool(args, ep.root)
        if c != 0:
            raise Halt("blocked", f"yt-sentinel {stk['name']}: {d.get('status')} {d.get('error')} {d.get('missing', '')}")
        outs += [f"{out}/provenance.json", f"{out}/grid.json"]
    return outs, f"{len(cfg.get('stacks', []))} stacks"


def run_script(ep, ctx):
    if not os.path.exists(ep.p("script.md")):
        packet(ep, "script", "# Task: script\n\nWrite `script.md`: American English, 6-9 minutes (about 900-1,300 words), chapters `## id: Title` matching episode.json. "
               "Every sentence with a number or strong word ends with {C#} (claims.json); media/org claims must contain their wording word ('reported'); hypotheses must be hedged; "
               "limitations end with {L}. Keep promised / reported / observed apart. Then run `facts.py --claims claims.json --script script.md --root .`.\n")
        raise Halt("needs_agent", "write script.md (see tasks/script.md)")
    c, d = tool([os.path.join(SK, "yt-facts", "facts.py"), "--claims", "claims.json", "--script", "script.md", "--root", "."], ep.root)
    if c != 0:
        raise Halt("blocked", "script vs claims: " + "; ".join(d.get("problems") or [d.get("error", "?")])[:500])
    return ["script.md"], f"{d['stats']['tagged_sentences']} tagged sentences, {len(d['used'])} claims used"


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


def run_voice(ep, ctx):
    script = ep.p("script.md")
    os.makedirs(ep.p("voice"), exist_ok=True)
    open(ep.p("voice", "spoken.md"), "w", encoding="utf-8").write(spoken_text(open(script, encoding="utf-8").read()))
    chars = len(open(ep.p("voice", "spoken.md"), encoding="utf-8").read())
    if os.path.exists(ep.p("voice", "narration.voice.json")) and os.path.exists(ep.p("voice", "narration.wav")):
        return ["voice/narration.wav", "voice/narration.voice.json"], "narration already generated (not regenerated)"
    plan = {"chars": chars, "script_sha256": sha(script), "provider": "elevenlabs", "voice": "Adam (pNInz6obpgDQGcFmaJgB)",
            "note": "PAID. Owner must create approvals/voice.json {approved:true, script_sha256, max_chars>=chars} and run with --allow-paid"}
    write_json(ep.p("voice", "plan.json"), plan)
    a, why = _approval(ep, "voice", plan["script_sha256"])
    if not a or not ctx["allow_paid"]:
        raise Halt("awaiting_approval", (why or "approval present but --allow-paid not given") + f"; plan: {chars} characters", ["voice/plan.json"])
    if ctx["dry"]:
        raise Halt("awaiting_approval", "dry-run: paid call not made", ["voice/plan.json"])
    if a.get("max_chars", 0) < chars:
        raise Halt("blocked", f"approved max_chars {a.get('max_chars')} < {chars} characters")
    c, d = tool([os.path.join(SK, "yt-voice", "voice.py"), "--script", "voice/spoken.md", "--output", "voice/narration.wav", "--auth", "proxy", "--confirm", "--max-chars", str(a["max_chars"])], ep.root)
    if c != 0:
        raise Halt("failed", f"yt-voice: {d.get('status')} {d.get('error')}")
    ctx["costs"].append({"stage": "voice", "chars": chars, "provider": "elevenlabs", "at": now(), "note": "approved by owner"})
    return ["voice/narration.wav", "voice/narration.voice.json"], f"generated {chars} chars"


def run_captions(ep, ctx):
    c, d = tool([os.path.join(SK, "yt-captions", "captions.py"), "--voice", "voice/narration.voice.json", "--out-dir", "captions", "--overwrite"], ep.root)
    if c != 0:
        raise Halt("blocked", f"yt-captions: {d.get('error') or d.get('status')}")
    return ["captions/captions.srt", "captions/captions.vtt", "captions/captions.json"], "captions built from real word timings"


def run_render(ep, ctx):
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


def run_qc(ep, ctx):
    c, d = tool([os.path.join(SK, "yt-qc", "qc.py"), "render/final.mp4", "--timeline", "timeline.json", "--profile", "long"], ep.root)
    write_json(ep.p("render", "qc.json"), d)
    if d.get("result") != "PASS":
        fails = [x["id"] for x in d.get("checks", []) if x.get("status") == "fail"]
        raise Halt("blocked", f"qc {d.get('result')}: {fails}", ["render/qc.json"])
    return ["render/qc.json"], "QC PASS"


def run_release(ep, ctx):
    e = ep.episode()
    st = ctx["state"]["stages"]
    pending = [s for s in STAGES if s != "release" and st.get(s, {}).get("status") != DONE]
    claims = json.load(open(ep.p("claims.json")))["claims"]
    L = [f"# Release package - {e.get('title', ep.slug)}", "", f"Generated {now()}. Nothing is published.", "",
         "## Status", *[f"- {s}: {st.get(s, {}).get('status', 'pending')} {st.get(s, {}).get('note', '')}" for s in STAGES if s != "release"], "",
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


RUN = {"topic": run_topic, "research": run_research, "facts": run_facts, "evidence": run_evidence, "script": run_script, "storyboard": run_storyboard,
       "visuals": run_visuals, "voice": run_voice, "captions": run_captions, "render": run_render, "qc": run_qc, "release": run_release}
# files whose change invalidates a stage (besides the outputs of its dependencies)
INPUTS = {"topic": ["topic/approval.json", "topic/candidates.json"], "research": ["claims.json"], "facts": ["claims.json"], "evidence": ["episode.json"],
          "script": ["script.md", "claims.json", "evidence/stack/provenance.json"], "storyboard": ["script.md", "episode.json", "claims.json", "evidence/stack/grid.json", "voice/narration.voice.json", "captions/captions.srt"],
          "visuals": ["episode.json", "graphics_spec.json", "evidence/stack/provenance.json"], "voice": ["script.md", "approvals/voice.json"],
          "captions": ["voice/narration.voice.json"], "render": ["timeline.json", "approvals/render.json"] , "qc": ["render/final.mp4", "timeline.json"],
          "release": ["claims.json", "story/report.md"]}


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
                if rec["status"] != DONE and not dry:
                    rec["status"], rec["note"] = "waiting", f"waiting for {blockers}"
                report[stage] = rec["status"]; continue
            ins = hashes(ep, ordered_inputs(ep, stage, st))
            cached = (stage != "release" and rec["status"] == DONE and not (force and (not only or stage == only)) and rec.get("inputs") == ins
                      and all(os.path.exists(ep.p(o)) and sha(ep.p(o)) == h for o, h in rec.get("outputs", {}).items()))
            if cached:
                report[stage] = "cached"; continue
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
                rec.update(status=DONE, finished=now(), note=note, inputs=ins, outputs=hashes(ep, outs), error=None)
                st["log"].append({"at": now(), "stage": stage, "event": "done", "note": note})
            except Halt as h:
                rec.update(status=h.status, finished=now(), note=h.note, error=h.note if h.status in ("blocked", "failed") else None, outputs=hashes(ep, h.outputs))
                st["log"].append({"at": now(), "stage": stage, "event": h.status, "note": h.note})
            except Exception as e:             # a bug or an environment failure is a blocked stage, never a traceback
                rec.update(status="failed", finished=now(), error=f"{type(e).__name__}: {e}")
                st["log"].append({"at": now(), "stage": stage, "event": "failed", "note": rec["error"]})
            report[stage] = rec["status"]
            ep.save(st)
            if os.environ.get("OA_STOP_AFTER") == stage:
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
           "next": {nxt: st["stages"][nxt].get("note")} if nxt else None, "dry_run": dry}
    return res, 0


def status(slug):
    ep = Ep(slug)
    st = ep.load()
    return {"slug": slug, "stages": {s: {"status": st["stages"].get(s, {}).get("status", "pending"), "note": st["stages"].get(s, {}).get("note")} for s in STAGES},
            "costs": st["costs"], "updated": st.get("updated")}, 0


def new(slug):
    slug = slug or "ep-" + time.strftime("%Y%m%d")
    ep = Ep(slug)
    os.makedirs(ep.p("topic"), exist_ok=True)
    if not os.path.exists(ep.p("episode.json")):
        write_json(ep.p("episode.json"), {"slug": slug, "title": "TBD", "titles": [], "grid": "evidence/stack/grid.json", "evidence": {"stacks": []}, "assets": {}, "chapters": []})
    return {"status": "ok", "slug": slug, "next": f"python3 .claude/skills/yt-orchestrate/orchestrate.py run --slug {slug}"}, 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("--slug")
    r = sub.add_parser("run"); r.add_argument("--slug", required=True); r.add_argument("--until", choices=STAGES); r.add_argument("--stage", choices=STAGES)
    r.add_argument("--force", action="store_true"); r.add_argument("--dry-run", action="store_true")
    r.add_argument("--allow-paid", action="store_true", help="permit yt-voice if approvals/voice.json matches the script")
    r.add_argument("--allow-render", action="store_true", help="permit the full render if approvals/render.json matches")
    s = sub.add_parser("status"); s.add_argument("--slug", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "new":
        res, code = new(a.slug)
    elif a.cmd == "status":
        res, code = status(a.slug)
    else:
        res, code = run(a.slug, a.until, a.stage, a.force, a.dry_run, a.allow_paid, a.allow_render)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
