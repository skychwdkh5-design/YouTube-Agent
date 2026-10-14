#!/usr/bin/env python3
"""guard.py - PreToolUse hook: stops the actions the owner reserved (exit code 2 = blocked, reason on stderr).

Blocked:
  - a direct paid TTS call (voice.py ... --confirm); the only path is `orbital.py run SLUG --stage tts --confirm`,
    which checks the owner's recorded approval first;
  - any git push that targets main/master, force pushes, and git commit while on main;
  - anything that uploads or publishes to YouTube;
  - edits to the finished EP001 / EP002 deliverables (productions/sahara-green/final, productions/dubai/final|release);
  - writing a key or token into a file.
The hook reads the tool call as JSON on stdin. It is a safety net against mistakes, not a security boundary:
the owner's approvals live in productions/<slug>/approvals.json.
"""
import json, re, subprocess, sys

PROTECTED = re.compile(r"(^|/)productions/(sahara-green/final|dubai/final|dubai/release)(/|$)")
SECRET = re.compile(r"(sk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|xi-api-key\s*[:=]\s*[A-Za-z0-9]{16,})")


def current_branch():
    try:
        return subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def check_bash(cmd, branch=None):
    if re.search(r"voice\.py", cmd) and "--confirm" in cmd and "orbital.py" not in cmd:
        return "paid TTS must go through orbital.py (owner approval + budget + cache). Direct voice.py --confirm is blocked."
    for m in re.finditer(r"git\s+push\b([^;&|]*)", cmd):
        args = m.group(1)
        if re.search(r"(--force|\s-f\b|--force-with-lease)", args) and re.search(r"\b(main|master)\b", args):
            return "force push to main is blocked."
        if re.search(r"(:|\s)(refs/heads/)?(main|master)\b", args) or re.search(r"\sorigin\s+(main|master)\b", " " + args):
            return "pushing to main is blocked; push your branch and open a PR."
        if not re.search(r"\borigin\b\s+\S+", args) and (branch or current_branch()) in ("main", "master"):
            return "you are on main; switch to a branch before pushing."
    if re.search(r"git\s+commit\b", cmd) and (branch or current_branch()) in ("main", "master"):
        return "never commit on main; create a branch first."
    if re.search(r"(youtube\.googleapis\.com/upload|videos\.insert|youtubeuploader|youtube-upload|studio\.youtube\.com/.*upload)", cmd, re.I):
        return "publishing to YouTube is the owner's decision; prepare the package instead."
    return None


def check_edit(path, content=""):
    if PROTECTED.search(path.replace("\\", "/")):
        return f"{path} is a finished EP001/EP002 deliverable - do not modify it (write a new file elsewhere)."
    if content and SECRET.search(content):
        return "refusing to write what looks like an API key or token into a file."
    return None


def decide(call, branch=None):
    tool, inp = call.get("tool_name", ""), call.get("tool_input", {}) or {}
    if tool == "Bash": return check_bash(inp.get("command", ""), branch)
    if tool in ("Edit", "Write", "MultiEdit"):
        return check_edit(inp.get("file_path", ""), inp.get("content", "") or inp.get("new_string", ""))
    return None


def main():
    try:
        call = json.load(sys.stdin)
    except ValueError:
        return 0
    msg = decide(call)
    if msg:
        print(f"[guard] {msg}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
