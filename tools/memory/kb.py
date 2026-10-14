#!/usr/bin/env python3
"""kb.py - the verified-solutions registry (the project's persistent memory of what was fixed).

    python3 tools/memory/kb.py validate [--strict]      # schema + every reference must exist
    python3 tools/memory/kb.py search WORDS...          # find an earlier solution before debugging
    python3 tools/memory/kb.py diagnose [FILE|-]        # match an error text against known symptoms
    python3 tools/memory/kb.py add ENTRY.json|-         # append one validated, non-duplicate entry
    python3 tools/memory/kb.py render [--check]         # write / verify docs/production-knowledge/SOLUTIONS.md
    python3 tools/memory/kb.py verify [--run-tests]     # list (or run) the regression tests of all entries
    python3 tools/memory/kb.py brief                    # short session-start summary

The registry is knowledge/solutions.json - the single source of truth. SOLUTIONS.md is generated from it
and never edited by hand. Every entry states the problem, its root cause, the fix that worked, when to
reuse it, where the code / commit / video example is, how it was verified, and a regression test (or the
reason none can exist). Output is JSON on stdout except `render` and `brief`.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTRY = os.path.join(ROOT, "knowledge", "solutions.json")
VIEW = os.path.join(ROOT, "docs", "production-knowledge", "SOLUTIONS.md")

STATUSES = ("VERIFIED", "HYPOTHESIS")
SCOPES = ("general", "EP001", "EP002")
AREAS = ("tts", "sync", "render", "qc", "visual", "geo", "storage", "process", "env", "research")
REQUIRED = ("id", "title", "status", "scope", "area", "date", "problem", "root_cause", "fix",
            "reuse_when", "refs", "verification")
REF_KEYS = ("code", "docs", "commits", "remote", "video")
STAGES = ("research", "claims", "script", "tts_plan", "tts", "captions", "storyboard", "render", "qc", "review", "package")
# which pipeline stages an entry matters for when it does not say (`stages` field overrides)
STAGE_AREAS = {"tts": ["tts_plan", "tts"], "sync": ["tts", "captions", "storyboard"], "render": ["storyboard", "render"], "qc": ["render", "qc", "review"],
               "visual": ["storyboard", "review"], "geo": ["claims", "storyboard"], "research": ["research", "claims"], "storage": ["render", "package"],
               "process": ["review", "package"], "env": []}
AUTOFIX_ENV_KEYS = ("PYTHONPATH", "LC_ALL", "PYTHONIOENCODING")
SECRET = re.compile(r"(sk_[A-Za-z0-9]{16,}|xi-api-key\s*[:=]\s*\S{8,}|ELEVENLABS_API_KEY\s*=\s*\S{8,}|ghp_[A-Za-z0-9]{20,})")


def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)


def load(path=REGISTRY):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("schema") != "orbitalatlas-solutions/1" or not isinstance(data.get("entries"), list):
        raise ValueError("registry must be {schema: 'orbitalatlas-solutions/1', entries: [...]}")
    return data


def _test_exists(spec):
    """'path/to/test_x.py::Class.test_name' - file exists and defines the test."""
    path, _, name = spec.partition("::")
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return f"regression test file missing: {path}"
    if name:
        leaf = name.split(".")[-1]
        with open(full, encoding="utf-8") as f:
            if not re.search(r"def\s+%s\b" % re.escape(leaf), f.read()):
                return f"regression test not defined in {path}: {leaf}"
    return None


def check_entry(e, strict=False):
    """Return (errors, warnings) for one entry."""
    errs, warns = [], []
    for k in REQUIRED:
        if k not in e or e[k] in ("", None, [], {}):
            errs.append(f"missing field '{k}'")
    if errs:
        return errs, warns
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", e["id"]):
        errs.append("id must be kebab-case, 3-61 chars")
    if e["status"] not in STATUSES: errs.append(f"status must be one of {STATUSES}")
    if e["scope"] not in SCOPES: errs.append(f"scope must be one of {SCOPES}")
    if e["area"] not in AREAS: errs.append(f"area must be one of {AREAS}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["date"]): errs.append("date must be YYYY-MM-DD")
    refs = e["refs"]
    if not isinstance(refs, dict) or not any(refs.get(k) for k in REF_KEYS):
        errs.append("refs needs at least one of code / docs / commits / remote / video")
        return errs, warns
    for k in ("code", "docs"):
        for p in refs.get(k, []):
            if not os.path.exists(os.path.join(ROOT, p)): errs.append(f"{k} ref not found: {p}")
    for c in refs.get("commits", []):
        if _git("cat-file", "-e", c + "^{commit}").returncode != 0:
            (errs if strict else warns).append(f"commit not in this clone (run: git fetch origin '+refs/heads/*:refs/remotes/origin/*'): {c}")
    for r in refs.get("remote", []):            # 'branch:path' - a file that lives on another branch
        br, _, p = r.partition(":")
        if _git("cat-file", "-e", f"origin/{br}:{p}").returncode != 0:
            (errs if strict else warns).append(f"remote ref not reachable (branch not fetched?): {r}")
    for v in refs.get("video", []):
        if not isinstance(v, str) or len(v) < 5: errs.append("video ref must describe episode + timecode/scene")
    if e["status"] == "VERIFIED":
        if "no_test_reason" not in e and not e.get("regression_test"):
            errs.append("VERIFIED needs regression_test or no_test_reason")
    if e.get("regression_test"):
        msg = _test_exists(e["regression_test"])
        if msg: errs.append(msg)
    if e.get("no_test_reason") and e.get("regression_test"):
        warns.append("both regression_test and no_test_reason given")
    for rx in e.get("symptoms", []):
        try: re.compile(rx)
        except re.error as x: errs.append(f"bad symptom regex {rx!r}: {x}")
    for st in e.get("stages", []):
        if st not in STAGES: errs.append(f"unknown stage {st!r} (one of {STAGES})")
    af = e.get("auto_fix")
    if af is not None:
        if not (isinstance(af, dict) and set(af) == {"env"} and isinstance(af["env"], dict) and af["env"]
                and all(k in AUTOFIX_ENV_KEYS and isinstance(v, str) for k, v in af["env"].items())):
            errs.append(f"auto_fix must be {{'env': {{KEY: value}}}} with KEY in {AUTOFIX_ENV_KEYS} ({{root}} = repo root); nothing else is applied automatically")
        elif not e.get("symptoms"):
            errs.append("auto_fix needs symptoms (it is applied only when an error matches them)")
    blob = json.dumps(e, ensure_ascii=False)
    if SECRET.search(blob): errs.append("entry looks like it contains a secret - never store keys")
    return errs, warns


def validate(strict=False, data=None):
    data = data or load()
    seen, problems, warnings = set(), [], []
    for e in data["entries"]:
        eid = e.get("id", "?")
        if eid in seen: problems.append(f"{eid}: duplicate id")
        seen.add(eid)
        errs, warns = check_entry(e, strict)
        problems += [f"{eid}: {m}" for m in errs]
        warnings += [f"{eid}: {m}" for m in warns]
    return {"ok": not problems, "entries": len(data["entries"]), "problems": problems, "warnings": warnings}


def _tokens(s):
    return set(re.findall(r"[a-z0-9]{3,}", s.lower()))


def _text(e):
    return " ".join(str(e.get(k, "")) for k in ("id", "title", "problem", "root_cause", "fix", "reuse_when", "area")) + " " + " ".join(e.get("symptoms", []))


def search(words, data=None):
    q = _tokens(" ".join(words))
    out = []
    for e in (data or load())["entries"]:
        score = len(q & _tokens(_text(e)))
        if score: out.append((score, e))
    out.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [{"id": e["id"], "title": e["title"], "status": e["status"], "scope": e["scope"], "fix": e["fix"], "score": s} for s, e in out]


def diagnose(text, data=None):
    hits = []
    for e in (data or load())["entries"]:
        for rx in e.get("symptoms", []):
            if re.search(rx, text, re.I | re.S):
                hits.append({"id": e["id"], "title": e["title"], "fix": e["fix"], "reuse_when": e["reuse_when"],
                             "status": e["status"], "matched": rx, **({"auto_fix": e["auto_fix"]} if e.get("auto_fix") else {})})
                break
    return hits


def for_stage(stage, data=None):
    """Known pitfalls to read BEFORE a pipeline stage runs: entries that name the stage, or whose area maps to it."""
    out = []
    for e in (data or load())["entries"]:
        st = e.get("stages") or STAGE_AREAS.get(e["area"], [])
        if stage in st:
            out.append({"id": e["id"], "title": e["title"], "status": e["status"], "fix": e["fix"], "reuse_when": e["reuse_when"]})
    return sorted(out, key=lambda x: (x["status"] != "VERIFIED", x["id"]))


def similar(entry, data):
    """Existing entries that probably describe the same thing (duplicate guard for `add`)."""
    t = _tokens(entry.get("title", "") + " " + entry.get("problem", ""))
    out = []
    for e in data["entries"]:
        u = _tokens(e["title"] + " " + e["problem"])
        if t and u and len(t & u) / len(t | u) >= 0.5: out.append(e["id"])
    return out


def add(entry, path=REGISTRY):
    data = load(path)
    if any(e["id"] == entry.get("id") for e in data["entries"]):
        return {"ok": False, "error": f"id exists: {entry.get('id')}"}
    errs, warns = check_entry(entry)
    if errs: return {"ok": False, "problems": errs}
    dup = similar(entry, data)
    if dup: return {"ok": False, "error": "looks like a duplicate of existing entries - extend one instead", "similar": dup}
    data["entries"].append(entry)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1); f.write("\n")
    os.replace(tmp, path)
    return {"ok": True, "id": entry["id"], "warnings": warns, "next": "run: python3 tools/memory/kb.py render"}


def render_md(data=None):
    data = data or load()
    L = ["# Verified solutions (generated - do not edit)",
         "",
         "Source of truth: `knowledge/solutions.json`. Regenerate with `python3 tools/memory/kb.py render`; "
         "`kb.py validate` checks every reference. Search before debugging: `kb.py search WORDS`, `kb.py diagnose FILE`.",
         "Status: **VERIFIED** = observed and checked in this repo; **HYPOTHESIS** = plausible, not proven.", ""]
    for area in AREAS:
        es = [e for e in data["entries"] if e["area"] == area]
        if not es: continue
        L += [f"## {area}", ""]
        for e in sorted(es, key=lambda x: x["id"]):
            r = e["refs"]
            refs = [f"`{p}`" for p in r.get("code", []) + r.get("docs", [])]
            refs += [f"commit `{c}`" for c in r.get("commits", [])]
            refs += [f"`{x}`" for x in r.get("remote", [])] + [f"video: {v}" for v in r.get("video", [])]
            test = f"`{e['regression_test']}`" if e.get("regression_test") else f"none - {e.get('no_test_reason', '')}"
            L += [f"### {e['id']} - {e['title']}",
                  f"*{e['status']} · {e['scope']} · {e['date']}*", "",
                  f"- **Problem:** {e['problem']}",
                  f"- **Root cause:** {e['root_cause']}",
                  f"- **Fix:** {e['fix']}",
                  f"- **Reuse when:** {e['reuse_when']}",
                  f"- **References:** {'; '.join(refs)}",
                  f"- **Verification:** {e['verification']}",
                  f"- **Regression test:** {test}", ""]
    return "\n".join(L).rstrip() + "\n"


def test_command(path):
    """How to run one registered test file. The orbitalatlas package tests must run as modules from the repo
    root (registry: orbitalatlas-tests-need-repo-root); every skill/tool test is a script run in its own folder."""
    if path.startswith("orbitalatlas/"):
        return [sys.executable, "-m", "unittest", path[:-3].replace("/", ".")], ROOT
    return [sys.executable, os.path.basename(path)], os.path.join(ROOT, os.path.dirname(path))


def run_tests(data=None, run=False):
    files = {}
    for e in (data or load())["entries"]:
        if e.get("regression_test"):
            files.setdefault(e["regression_test"].partition("::")[0], []).append(e["id"])
    res = []
    for path, ids in sorted(files.items()):
        row = {"file": path, "entries": ids}
        if run:
            cmd, cwd = test_command(path)
            r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            row["passed"] = r.returncode == 0
            if r.returncode: row["tail"] = (r.stdout + r.stderr)[-600:]
        res.append(row)
    return res


def brief():
    d = load()
    v = validate()
    by = {}
    for e in d["entries"]: by[e["area"]] = by.get(e["area"], 0) + 1
    br = _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    lines = [f"[memory] {len(d['entries'])} verified solutions ({', '.join(f'{k}:{n}' for k, n in sorted(by.items()))}); registry {'OK' if v['ok'] else 'HAS PROBLEMS - run kb.py validate'}.",
             "[memory] Before debugging: kb.py search WORDS / kb.py diagnose FILE. After a verified fix: kb.py add ENTRY.json, then kb.py render.",
             "[memory] Index: docs/production-knowledge/README.md. Autopilot: python3 tools/autopilot/orbital.py status SLUG."]
    if br in ("main", "master"):
        lines.append("[memory] WARNING: on main - never commit to main; work on a branch.")
    return "\n".join(lines)


def _read_json_arg(a):
    if a == "-": return json.loads(sys.stdin.read())
    with open(a, encoding="utf-8") as f: return json.load(f)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return 0
    cmd, rest = a[0], a[1:]
    try:
        if cmd == "validate":
            r = validate(strict="--strict" in rest); print(json.dumps(r, indent=1)); return 0 if r["ok"] else 1
        if cmd == "search":
            print(json.dumps(search(rest), indent=1, ensure_ascii=False)); return 0
        if cmd == "diagnose":
            if not rest or rest[0] == "-": text = sys.stdin.read()
            else:
                with open(rest[0], encoding="utf-8", errors="replace") as f: text = f.read()
            print(json.dumps(diagnose(text), indent=1, ensure_ascii=False)); return 0
        if cmd == "add":
            r = add(_read_json_arg(rest[0])); print(json.dumps(r, indent=1)); return 0 if r["ok"] else 1
        if cmd == "render":
            md = render_md()
            if "--check" in rest:
                cur = ""
                if os.path.exists(VIEW):
                    with open(VIEW, encoding="utf-8") as f: cur = f.read()
                ok = cur == md
                print(json.dumps({"ok": ok, "stale": not ok})); return 0 if ok else 1
            os.makedirs(os.path.dirname(VIEW), exist_ok=True)
            with open(VIEW, "w", encoding="utf-8") as f: f.write(md)
            print(json.dumps({"ok": True, "wrote": os.path.relpath(VIEW, ROOT)})); return 0
        if cmd == "verify":
            r = run_tests(run="--run-tests" in rest); print(json.dumps(r, indent=1))
            return 0 if all(x.get("passed", True) for x in r) else 1
        if cmd == "brief":
            print(brief()); return 0
    except (OSError, ValueError, json.JSONDecodeError) as x:
        print(json.dumps({"ok": False, "error": str(x)})); return 2
    print(json.dumps({"ok": False, "error": f"unknown command {cmd}"})); return 2


if __name__ == "__main__":
    sys.exit(main())
