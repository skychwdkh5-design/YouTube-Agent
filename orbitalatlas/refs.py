"""Reference library loader and validator (docs/references/library).

    python3 -m orbitalatlas.refs validate        # schema, unique ids, implementation symbols that really exist
    python3 -m orbitalatlas.refs list [--status S]
    python3 -m orbitalatlas.refs consult SCENE_TYPE [--implemented]   # the effects + QA rules a storyboard should consult for a kind of scene

Layout: library/sources.json (one entry per reference video; never edited once registered) + library/effects/<REF_ID>.json (one file per reference, so a new
reference never overwrites an old one). `validate` fails on duplicate effect ids across files, a missing source, an effect whose `implementation` names a
module.symbol that does not exist (unless the status is NOT_IMPLEMENTED), or an IMPLEMENTED effect without QA rules. Extend by adding a source + a file."""
# effect-reuse-checked: knowledge/effects.json lists what RENDERERS can do; this library records what the REFERENCES showed and which of it is implemented.
import glob
import importlib
import json
import os
import re
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "references", "library")
REQUIRED = ("id", "ref", "timestamp", "description", "visual_purpose", "animation_behavior", "timing", "parameters", "dependencies", "implementation", "status", "preset", "scene_types", "qa_rules", "uncertainty")
STATUSES = ("IMPLEMENTED", "PARTIAL", "NOT_IMPLEMENTED")


def sources(lib=LIB): return json.load(open(os.path.join(lib, "sources.json"), encoding="utf-8"))["sources"]


def effects(lib=LIB):
    out = []
    for f in sorted(glob.glob(os.path.join(lib, "effects", "*.json"))): out += json.load(open(f, encoding="utf-8"))["effects"]
    return out


def _resolve(sym):
    """'module.attr' or 'module.Class.attr' under orbitalatlas; text after a space or '(' is a comment. Returns True when the symbol exists."""
    s = re.split(r"[\s(]", sym.strip())[0]
    parts = s.split(".")
    for i in range(len(parts), 0, -1):
        try: mod = importlib.import_module("orbitalatlas." + ".".join(parts[:i]))
        except ImportError: continue
        obj = mod
        for p in parts[i:]:
            if not hasattr(obj, p): return False
            obj = getattr(obj, p)
        return True
    return False


def validate(lib=LIB):
    probs, ids = [], set(); srcs = {s["id"]: s for s in sources(lib)}
    for s in srcs.values():
        for k in ("id", "title", "sha256", "container", "what_it_is", "analysis", "effects_file", "limits"):
            if not s.get(k): probs.append(f"source {s.get('id')}: missing {k}")
        for k in ("analysis", "effects_file"):
            if s.get(k) and not os.path.exists(os.path.join(lib, s[k])): probs.append(f"source {s['id']}: {k} file {s[k]} not found")
    for e in effects(lib):
        miss = [k for k in REQUIRED if k not in e or e[k] in (None, "")]
        if miss: probs.append(f"{e.get('id')}: missing {miss}")
        if e.get("id") in ids: probs.append(f"duplicate effect id {e['id']}")
        ids.add(e.get("id"))
        if e.get("ref") not in srcs: probs.append(f"{e.get('id')}: unknown reference {e.get('ref')}")
        if e.get("status") not in STATUSES: probs.append(f"{e.get('id')}: bad status {e.get('status')}")
        if e.get("status") in ("IMPLEMENTED", "PARTIAL"):
            if not e.get("implementation"): probs.append(f"{e['id']}: {e['status']} but no implementation")
            for sym in e.get("implementation", []):
                if not _resolve(sym): probs.append(f"{e['id']}: implementation {sym!r} does not exist")
            if e["status"] == "IMPLEMENTED" and not e.get("qa_rules"): probs.append(f"{e['id']}: IMPLEMENTED without qa_rules")
        if not str(e.get("uncertainty", "")).strip(): probs.append(f"{e.get('id')}: uncertainty must be stated (use '-' only when exact)")
    return probs


def consult(scene_type, implemented_only=False, lib=LIB):
    q = scene_type.lower(); out = []
    for e in effects(lib):
        if implemented_only and e["status"] == "NOT_IMPLEMENTED": continue
        if any(q in t.lower() or t.lower() in q for t in e["scene_types"]): out.append(dict(id=e["id"], ref=e["ref"], status=e["status"], preset=e["preset"], qa_rules=e["qa_rules"], description=e["description"]))
    return out


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] not in ("validate", "list", "consult"): print(__doc__); return 0
    if a[0] == "validate":
        p = validate(); print(json.dumps(dict(ok=not p, effects=len(effects()), sources=len(sources()), problems=p), indent=1)); return 1 if p else 0
    if a[0] == "list":
        st = a[a.index("--status") + 1] if "--status" in a else None
        for e in effects():
            if st is None or e["status"] == st: print(e["id"], e["status"], "|", e["description"][:90])
        return 0
    print(json.dumps(consult(a[1], "--implemented" in a), indent=1)); return 0


if __name__ == "__main__":
    sys.exit(main())
