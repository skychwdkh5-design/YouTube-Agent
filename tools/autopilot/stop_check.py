#!/usr/bin/env python3
"""stop_check.py - Stop hook: before the session ends, (1) the finished EP001/EP002 files must be untouched and
(2) a fix that was made must also be written to the memory. Exit 2 = Claude is told once and continues; the second
time (stop_hook_active) the hook lets the session end, so it can never loop.

The reminder fires when the work not yet pushed (unpushed commits + uncommitted changes) looks like a fix - a commit
message with fix/bug/regression/repair, or a Python/JS change under .claude/skills, orbitalatlas, tools or productions -
and knowledge/solutions.json was not changed. Opt out per commit with `memory: n/a` in the message, or per session by
adding the entry. Reading the registry is not enough: the lesson has to be recorded with a regression test.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import protected  # noqa: E402

FIX_WORDS = re.compile(r"\b(fix|fixed|fixes|bug|regression|repair|repaired|workaround|root cause)\b", re.I)
CODE = re.compile(r"\.(py|js|mjs|sh)$")
CODE_DIRS = re.compile(r"^(\.claude/skills|orbitalatlas|tools|productions/[^/]+/(preview|motion|engine))/")
REGISTRY = "knowledge/solutions.json"


def memory_reminder(messages, changed_files):
    """Pure decision: should the agent be told to record a verified fix? Returns a message or None."""
    if REGISTRY in changed_files: return None
    if any("memory: n/a" in m.lower() for m in messages): return None
    fixy = any(FIX_WORDS.search(m) for m in messages)
    code = [f for f in changed_files if CODE.search(f) and CODE_DIRS.search(f) and not re.search(r"(^|/)test_[^/]*$", f)]
    if fixy and code:
        return ("The unpushed work contains a fix (" + ", ".join(code[:3]) + ") but knowledge/solutions.json was not changed. "
                "Record the verified fix: problem, root cause, fix, reuse condition, reference, verification, regression test "
                "(`python3 tools/memory/kb.py add ENTRY.json && python3 tools/memory/kb.py render`), or add `memory: n/a` to the commit message if it is not a reusable lesson.")
    return None


def _git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)


def unpushed():
    if _git("rev-parse", "--abbrev-ref", "@{u}").returncode != 0: return [], []
    msgs = _git("log", "@{u}..HEAD", "--format=%B").stdout.split("\n\n")
    files = set(_git("diff", "--name-only", "@{u}", "HEAD").stdout.split()) | set(_git("diff", "--name-only").stdout.split()) | set(_git("diff", "--name-only", "--cached").stdout.split())
    return msgs, sorted(files)


def main():
    try: call = json.load(sys.stdin)
    except ValueError: call = {}
    if call.get("stop_hook_active"): return 0
    problems = []
    v = protected.verify()
    if not v["ok"]:
        problems.append("Finished EP001/EP002 files differ from their release: " + json.dumps(v["violations"][:5]))
    msgs, files = unpushed()
    m = memory_reminder(msgs, files)
    if m: problems.append(m)
    if problems:
        print("[stop-check] " + " | ".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
