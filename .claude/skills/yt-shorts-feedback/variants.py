#!/usr/bin/env python3
"""variants.py - build single-variable variants of a timeline v3 Short (first 1-3 seconds, loop ending) without touching yt-render.

    python3 variants.py build spec.json [--out-dir DIR] [--validate --media-root DIR]
    python3 variants.py first-seconds timeline.json [--seconds 3] [--voice-meta narration.voice.json]
    python3 variants.py loop-close timeline.json --start 49.5 [--out loop_timeline.json] [--validate --media-root DIR]

`build` reads a spec, copies the base timeline once per variant and applies ONLY the overrides the spec lists for the declared variable shots
(camera, layers, info, visual_family). Everything else - narration, captions, every other shot, the end - must stay byte-identical, and the tool
checks that. A variant that needs a different spoken line is refused: that is a new TTS take (paid), which needs the user's explicit approval and
is outside this tool. Nothing renders; `--validate` runs `render.py` WITHOUT --confirm, which only checks the timeline and prints its plan.

spec.json
{"experiment_id": "EXP-001", "factor": "first_3s", "base_timeline": "timeline.json", "variable_shots": ["hook"],
 "variants": [{"id": "A", "name": "outcome_first", "set": {"hook": {"camera": {...}, "layers": [...], "info": "..."}}},
              {"id": "B", "name": "orientation_first", "set": {"hook": {...}}}]}
"""
import argparse, copy, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); RENDER = os.path.join(HERE, "..", "yt-render", "render.py")
ALLOWED_SET_KEYS = ("camera", "layers", "info", "visual_family")
FORBIDDEN_SET_KEYS = {"claims": "claims are verified for the base story; a variant may not change them", "start": "shot timing is part of the story, not of the first-seconds variable",
                      "id": "shot ids are referenced by the experiment record", "spoken": "a different spoken line needs a new TTS take (paid, needs explicit approval)",
                      "voice": "a different voice take needs explicit approval", "captions": "captions are shared by every variant"}

class VarError(Exception):
    pass

def load(path):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except (OSError, json.JSONDecodeError) as e: raise VarError(f"cannot read {path}: {e}")

def apply_variant(base, variant, variable_shots):
    tl = copy.deepcopy(base); shots = {s.get("id"): s for s in tl.get("shots", [])}
    for sid, changes in (variant.get("set") or {}).items():
        if sid not in variable_shots: raise VarError(f"variant {variant.get('id')}: shot '{sid}' is not a declared variable shot {variable_shots}")
        if sid not in shots: raise VarError(f"variant {variant.get('id')}: the base timeline has no shot '{sid}'")
        for k, v in changes.items():
            if k in FORBIDDEN_SET_KEYS: raise VarError(f"variant {variant.get('id')}: '{k}' cannot be overridden: {FORBIDDEN_SET_KEYS[k]}")
            if k not in ALLOWED_SET_KEYS: raise VarError(f"variant {variant.get('id')}: unknown override '{k}' (allowed: {ALLOWED_SET_KEYS})")
            shots[sid][k] = copy.deepcopy(v)
    return tl

def frozen_parts(tl, variable_shots):
    """everything that must be identical across variants"""
    other = [s for s in tl.get("shots", []) if s.get("id") not in variable_shots]
    var_fixed = [{k: s.get(k) for k in ("id", "start", "claims")} for s in tl.get("shots", []) if s.get("id") in variable_shots]
    rest = {k: v for k, v in tl.items() if k not in ("shots", "assets")}
    return {"other_shots": other, "variable_shots_fixed_fields": var_fixed, "everything_else": rest}

def check_single_variable(base, built, variable_shots):
    """returns a list of violations (empty = the variants differ only in the declared variable shots' camera/layers/info/visual_family)"""
    bad, ref = [], frozen_parts(base, variable_shots)
    for vid, tl in built.items():
        got = frozen_parts(tl, variable_shots)
        for part in ref:
            if json.dumps(ref[part], sort_keys=True) != json.dumps(got[part], sort_keys=True): bad.append(f"variant {vid}: '{part}' differs from the base timeline")
        for a, b in (("assets", "assets"),):
            added = set(tl.get(a, {})) - set(base.get(a, {})); removed = set(base.get(a, {})) - set(tl.get(a, {}))
            if removed: bad.append(f"variant {vid}: assets removed: {sorted(removed)}")
            if any(json.dumps(tl[a][k], sort_keys=True) != json.dumps(base[a][k], sort_keys=True) for k in set(base.get(a, {})) & set(tl.get(a, {}))): bad.append(f"variant {vid}: an existing asset was redefined")
    return bad

def plan_of(path, root=None):
    """runs render.py WITHOUT --confirm: validation + plan only, nothing is rendered."""
    cmd = [sys.executable, RENDER, "--timeline", path] + (["--media-root", root] if root else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    try: doc = json.loads(r.stdout)
    except json.JSONDecodeError: raise VarError(f"render.py gave no JSON: {r.stdout[:200]} {r.stderr[:200]}")
    if doc.get("status") != "confirm_required": return {"valid": False, "status": doc.get("status"), "error": doc.get("error")}
    p = doc.get("plan", {}); return {"valid": True, "duration": p.get("duration"), "compositions": p.get("compositions"), "visual_novelty": p.get("visual_novelty"), "warnings": p.get("warnings")}

def first_seconds(tl, seconds=3.0, words=None):
    """what the viewer sees in the first seconds, from the timeline text only (numeric starts; word anchors need the voice meta)"""
    def start_of(s):
        st = s.get("start")
        if isinstance(st, (int, float)): return float(st)
        if isinstance(st, dict) and words is not None and st.get("word", None) is not None and st["word"] < len(words):
            w = words[st["word"]]; return float(w.get("start" if st.get("edge", "start") == "start" else "end", 0)) + float(st.get("offset", 0))
        return None
    out = []
    for s in tl.get("shots", []):
        st = start_of(s)
        if st is None: out.append({"id": s.get("id"), "start": None, "note": "word-anchored start: pass --voice-meta to resolve it"}); continue
        if st < seconds:
            layers = [{"type": L.get("type"), "t": L.get("t"), "text": L.get("text"), "asset": L.get("asset")} for L in s.get("layers", [])]
            out.append({"id": s["id"], "start": st, "visual_family": s.get("visual_family"), "info": s.get("info"), "camera": s.get("camera"), "layers": layers})
    return out

def close_loop(tl, start, hold=None):
    """append a closing shot whose camera ends on the first shot's opening view and whose layers repeat the first shot's opening layers"""
    tl = copy.deepcopy(tl); shots = tl.get("shots", [])
    if len(shots) < 2: raise VarError("need at least two shots to close a loop")
    first, prev = shots[0], shots[-1]
    if any(s.get("id") == "loop_return" for s in shots): raise VarError("the timeline already has a 'loop_return' shot")
    fcam = first.get("camera") or {}; opening = fcam.get("from") or fcam.get("to") or fcam
    pcam = prev.get("camera") or {}; resting = pcam.get("to") or pcam.get("from") or pcam
    if not opening: raise VarError("the first shot has no camera to return to")
    last_start = shots[-1].get("start")
    if isinstance(last_start, (int, float)) and start <= last_start: raise VarError(f"--start {start} must come after the last shot's start ({last_start})")
    layers = [copy.deepcopy(L) for L in first.get("layers", []) if L.get("t") in (None, [0, 0]) or (isinstance(L.get("t"), list) and L["t"][0] == 0)]
    for L in layers: L.pop("t", None)
    shot = {"id": "loop_return", "start": start, "info": "loop seam: return to the opening view", "camera": {"from": copy.deepcopy(resting), "to": copy.deepcopy(opening)}, "layers": layers}
    if first.get("visual_family"): shot["visual_family"] = first["visual_family"]
    shots.append(shot); return tl

def _write(path, doc):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f: json.dump(doc, f, indent=1, ensure_ascii=False); f.write("\n")
    os.replace(tmp, path)

def cmd_build(a):
    spec = load(a.spec); base_path = spec["base_timeline"] if os.path.isabs(spec["base_timeline"]) else os.path.join(os.path.dirname(os.path.abspath(a.spec)), spec["base_timeline"])
    base = load(base_path); vshots = spec.get("variable_shots") or [base["shots"][0]["id"]]
    if len(spec.get("variants", [])) < 2: raise VarError("a spec needs at least two variants")
    ids = [v["id"] for v in spec["variants"]]
    if len(set(ids)) != len(ids): raise VarError("variant ids must be unique")
    built = {v["id"]: apply_variant(base, v, vshots) for v in spec["variants"]}
    bad = check_single_variable(base, built, vshots)
    if bad: raise VarError("not a single-variable test: " + "; ".join(bad))
    same = [i for i in ids for j in ids if i < j and json.dumps(built[i], sort_keys=True) == json.dumps(built[j], sort_keys=True)]
    if same: raise VarError(f"variants {same} are identical to another variant: nothing is being tested")
    out_dir = a.out_dir or os.path.dirname(os.path.abspath(a.spec)); res = {"status": "ok", "experiment_id": spec.get("experiment_id"), "factor": spec.get("factor"), "variants": {}}
    for vid, tl in built.items():
        p = os.path.join(out_dir, f"timeline.{vid}.json"); _write(p, tl); entry = {"timeline": p, "first_seconds": first_seconds(tl, 3.0)}
        if a.validate: entry["plan"] = plan_of(p, a.media_root or os.path.dirname(base_path))
        res["variants"][vid] = entry
    print(json.dumps(res, indent=1, ensure_ascii=False)); return 0

def cmd_first(a):
    tl = load(a.timeline); words = None
    if a.voice_meta: m = load(a.voice_meta); words = m.get("words") if isinstance(m, dict) else m
    print(json.dumps({"status": "ok", "seconds": a.seconds, "shots": first_seconds(tl, a.seconds, words)}, indent=1, ensure_ascii=False)); return 0

def cmd_loop(a):
    tl = close_loop(load(a.timeline), a.start); out = a.out or os.path.splitext(a.timeline)[0] + ".loop.json"; _write(out, tl)
    res = {"status": "ok", "timeline": out, "declared_strategy": "visual_return", "closing_shot": "loop_return", "next": "render, then: python3 loopcheck.py --video short.mp4 --captions ... --declared visual_return"}
    if a.validate: res["plan"] = plan_of(out, a.media_root or os.path.dirname(os.path.abspath(a.timeline)))
    print(json.dumps(res, indent=1, ensure_ascii=False)); return 0

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("spec.json")[0].strip(), formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("build"); p.add_argument("spec"); p.add_argument("--out-dir"); p.add_argument("--validate", action="store_true"); p.add_argument("--media-root"); p.set_defaults(f=cmd_build)
    p = sub.add_parser("first-seconds"); p.add_argument("timeline"); p.add_argument("--seconds", type=float, default=3.0); p.add_argument("--voice-meta"); p.set_defaults(f=cmd_first)
    p = sub.add_parser("loop-close"); p.add_argument("timeline"); p.add_argument("--start", type=float, required=True); p.add_argument("--out"); p.add_argument("--validate", action="store_true"); p.add_argument("--media-root"); p.set_defaults(f=cmd_loop)
    try:
        a = ap.parse_args(argv)
        if not getattr(a, "f", None): print(__doc__); return 0
        return a.f(a)
    except (VarError, KeyError, OSError) as e:
        print(json.dumps({"status": "error", "error": f"{type(e).__name__}: {e}"}, indent=1)); return 2

if __name__ == "__main__":
    sys.exit(main())
