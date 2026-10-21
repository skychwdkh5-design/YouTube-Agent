#!/usr/bin/env python3
"""produce.py - one command from a chosen topic to a 720p preview of the whole film (never the final master, never a publish).

    python produce.py --topic "NEOM The Line" --slug neom-line --preview            # replay / continue: everything cached is reused
    python produce.py --topic "..." --preview --jobs 4
    python produce.py --topic "..." --budget-chars 6000 --preview                   # the owner's pre-approved voice budget (characters); without it voice stays behind approvals/voice.json

Chain (existing modules, nothing re-invented):
  research -> fact check -> script            yt-orchestrate stages; these need Claude. When one is missing produce.py STOPS and says exactly which task file to fill (exit 2), then continues on the next run.
  voice (paid, only within the budget)         yt-voice via the orchestrator's single-use approval ledger
  media search                                 yt-media-research/media_cache.py (probe cache, licence cache, visible exceptions)
  scene planning + motion graphics             yt-visual-planner (notes: infographics / maps / scenes from yt-storyboard/scene_templates.py + motion_presets.json)
  preview render + QC                          yt-orchestrate/preview.py (chapters in parallel, per-chapter cache, automatic QC)
Writes productions/<slug>/produce.config.json (topic, sources, scenes, voice, timestamps) and produce_log.json (seconds per step, agent steps, what needs the owner).
Model calls and tokens are NOT measurable from this process: the log says so.
"""
import argparse, hashlib, json, os, re, subprocess, sys, time

REPO = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(REPO, ".claude", "skills")
PY = sys.executable
ORCH = os.path.join(SK, "yt-orchestrate", "orchestrate.py")


def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40] or "episode"


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, **kw)


def j(s):
    try:
        return json.loads(s)
    except ValueError:
        return None


class Log:
    def __init__(self):
        self.t0 = time.time(); self.steps = []

    def step(self, name, fn):
        t = time.time(); r = fn()
        self.steps.append({"step": name, "seconds": round(time.time() - t, 1)})
        return r


def config(root, topic, slug, args):
    p = os.path.join(root, "produce.config.json")
    cfg = json.load(open(p)) if os.path.exists(p) else {}
    notes = json.load(open(os.path.join(root, "research", "notes.json"))) if os.path.exists(os.path.join(root, "research", "notes.json")) else {}
    cfg.update({"schema": "produce-config/1", "topic": topic, "slug": slug, "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "budget_chars": args.budget_chars, "paid_allowed": bool(args.budget_chars),
                "sources": {"claims": "claims.json", "ledger": "media/ledger.json", "licence_cache": "media_cache/index.json", "exceptions": "media/exceptions.json"},
                "scenes": {"infographics": len(notes.get("infographics") or []), "maps": len(notes.get("maps") or []), "templates": len(notes.get("scenes") or [])},
                "voice": "voice/narration.voice.json", "timeline": "timeline.json", "preview": f"render/{slug}_preview_720p.mp4"})
    json.dump(cfg, open(p, "w"), indent=1)
    return cfg


def grant_voice_budget(root, budget):
    """The owner's pre-approved budget: a single-use approval is written only if the validated script fits it (characters). Without --budget-chars nothing is written."""
    plan = os.path.join(root, "voice", "plan.json")
    if not os.path.exists(plan):
        return "no voice plan yet"
    pl = json.load(open(plan))
    if pl["chars"] > budget:
        return f"script is {pl['chars']} characters, over the pre-approved budget {budget}: STOP, owner decision needed"
    ap = os.path.join(root, "approvals", "voice.json")
    if os.path.exists(ap) and json.load(open(ap)).get("script_sha256") == pl["script_sha256"]:
        return "approval already on file"
    os.makedirs(os.path.dirname(ap), exist_ok=True)
    json.dump({"approved": True, "script_sha256": pl["script_sha256"], "max_chars": pl["chars"] + 10, "approval_id": f"AUTO-{pl['script_sha256'][:8]}",
               "note": f"written by produce.py inside the owner's pre-approved budget of {budget} characters; single use"}, open(ap, "w"), indent=1)
    return "approval written inside the pre-approved budget"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--topic", required=True); ap.add_argument("--slug"); ap.add_argument("--preview", action="store_true")
    ap.add_argument("--jobs", type=int, default=4); ap.add_argument("--budget-chars", type=int, default=0); ap.add_argument("--force-preview", action="store_true")
    a = ap.parse_args(argv)
    slug = a.slug or slugify(a.topic)
    root = os.path.join(REPO, "productions", slug)
    L = Log()
    if not os.path.exists(os.path.join(root, "state.json")):
        L.step("new", lambda: sh([PY, ORCH, "new", "--slug", slug]))
    stop = None
    notes_p = os.path.join(root, "research", "notes.json")
    ms = {}
    if os.path.exists(notes_p):
        ms = json.load(open(notes_p)).get("media_scenes") or {}
    media = {"skipped": "notes.json has no media_scenes (queries come from the planning step)"}
    if ms:                       # media search: probe cache, licence cache, search, verify, fetch, visible exceptions
        media = L.step("media_search", lambda: j(sh([PY, os.path.join(SK, "yt-media-research", "media_cache.py"), "auto", "--root", root]).stdout) or {"error": "media_cache failed"})
    voice_msg = None
    if a.budget_chars:
        voice_msg = grant_voice_budget(root, a.budget_chars)
    run_args = [PY, ORCH, "run", "--slug", slug] + (["--allow-paid"] if a.budget_chars else [])
    res = L.step("pipeline", lambda: j(sh(run_args).stdout))
    st = (res or {}).get("stages", {})
    nxt = (res or {}).get("next") or {}
    agent = [k for k, v in st.items() if v == "needs_agent"]
    blocked = [k for k, v in st.items() if v in ("blocked",)]
    cfg = config(root, a.topic, slug, a)
    out = {"slug": slug}
    if agent or blocked:
        stop = {"needs_claude": agent, "blocked": blocked, "detail": {k: str(nxt.get(k, ""))[:140] for k in agent + blocked}}
    elif a.preview and all(st.get(s) in ("done", "cached") for s in ("visualcheck", "voice", "voicecheck", "captions")):
        sys.path.insert(0, os.path.join(SK, "yt-orchestrate"))
        import preview
        rep = L.step("preview_render_qc", lambda: preview.build(slug, a.jobs, a.force_preview))
        out["preview"] = rep
    elif a.preview:
        stop = {"waiting_for": [k for k in ("visualcheck", "voice", "voicecheck", "captions") if st.get(k) not in ("done", "cached")], "voice": voice_msg or "voice stays behind the owner's approval (no --budget-chars)"}
    total = round(time.time() - L.t0, 1)
    exc = []
    ep = os.path.join(root, "media", "exceptions.json")
    if os.path.exists(ep):
        exc = [x["chapter"] for x in json.load(open(ep)).get("exceptions", [])]
    log = {"slug": slug, "total_seconds": total, "steps": L.steps, "media": media, "stopped": stop, "visual_standard_exceptions": exc,
           "claude_model_calls": "not measurable from code (this process makes none; agent steps are listed under 'stopped')", "tokens": "not available",
           "owner_needed": ["final render (--allow-render)", "publish (never automatic)"] + (["voice approval"] if not a.budget_chars and st.get("voice") not in ("done", "cached") else [])}
    json.dump(log, open(os.path.join(root, "produce_log.json"), "w"), indent=1)
    lines = [f"produce {slug}: {total}s total | " + ", ".join(f"{s['step']} {s['seconds']}s" for s in L.steps)]
    if "preview" in out:
        r = out["preview"]
        lines += [f"preview: {r['output']} | QC {r['qc']} | render wall {r['render_wall_s']}s with {r['jobs']} jobs | chapters rendered {sum(1 for c in r['chapters'].values() if not c['cached'])}/{len(r['chapters'])} (rest from cache)"]
    if stop:
        lines += [f"STOPPED: {json.dumps(stop)[:300]}"]
    lines += [f"media: {json.dumps(media)[:200]}", f"visual-standard exceptions: {exc or 'none recorded'}", "owner needed: " + ", ".join(log["owner_needed"]), "model calls/tokens: not measurable here"]
    print("\n".join(lines[:15]))
    return 2 if (stop and (stop.get("needs_claude") or stop.get("blocked"))) else 0


if __name__ == "__main__":
    sys.exit(main())
