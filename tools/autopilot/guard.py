#!/usr/bin/env python3
"""guard.py - PreToolUse hook: stops the actions the owner reserved (exit code 2 = blocked, reason on stderr).

Layers (a text filter alone is not a defence, so the hard limits also live in the code that acts):
  1. this hook - Bash commands are split into real commands and tokenised, so a string mentioned inside a heredoc or an
     echo is not a command, while `sh -c`, `cd x && python voice.py`, `env X=1 python ...` and pipes are still seen;
     file tools (Edit/Write/MultiEdit) and the GitHub MCP tools are checked too;
  2. yt-voice's own approval_gate (voice.py): the paid request is refused inside the function that makes it, whatever
     command, script or import reached it;
  3. tools/autopilot/protected.py: a diff check that finished EP001/EP002 deliverables are byte-identical to their release refs.

Blocked here:
  - paid TTS outside orbital.py, and direct calls to ElevenLabS generation endpoints (curl, wget, python -c ...);
  - git push that targets main/master (any refspec form), force pushes, git commit on main, `git push --mirror/--all`;
  - GitHub MCP: merge_pull_request / enable_pr_auto_merge (the owner merges), pushing or editing files on main;
  - anything that uploads or publishes to YouTube;
  - writes (redirect, tee, sed -i, rm, mv, cp, git checkout/restore ...) to finished EP001/EP002 deliverables, and Edit/Write there;
  - secrets written into files, and new scripts that call the paid generation API;
  - a NEW effect/engine file that duplicates an effect in knowledge/effects.json (add `# effect-reuse-checked: why` to override).
The hook reads the tool call as JSON on stdin. It is a safety net against mistakes and alternative paths, not a security
boundary against someone who edits the hook; the owner's approvals live in productions/<slug>/approvals.json.
"""
import json, os, re, shlex, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools", "memory"))

PROTECTED = re.compile(r"(?:^|[/\s'\"=:])productions/(?:sahara-green/final|dubai/final|dubai/release)(?:/|\s|$|['\"])")
SECRET = re.compile(r"(sk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|xi-api-key\s*[:=]\s*[A-Za-z0-9]{16,})")
PAID_API = re.compile(r"elevenlabs\.io/v\d+/(text-to-speech|sound-generation|speech-to-speech|dubbing|music|text-to-voice|voice-generation|voices/add)", re.I)
YOUTUBE_UP = re.compile(r"(youtube\.googleapis\.com/upload|googleapis\.com/upload/youtube|videos\.insert|youtubeuploader|youtube-upload|studio\.youtube\.com/.*upload)", re.I)
WRITERS = {"rm", "mv", "cp", "tee", "truncate", "dd", "sponge", "shred", "ln", "install", "rsync", "touch", "chmod", "unlink"}
MAIN = r"(?:refs/heads/)?(?:main|master)"
CODE_DIRS = re.compile(r"(^|/)(orbitalatlas|tools|\.claude/skills|productions/[^/]+/(preview|motion|engine|scenes))/")


def current_branch():
    try:
        return subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def _split_unquoted(cmd):
    """Split on ; & | && || and newlines that are NOT inside quotes (a quoted body such as sh -c '...; ...' stays whole)."""
    parts, cur, q, i = [], [], None, 0
    while i < len(cmd):
        c = cmd[i]
        if q:
            cur.append(c)
            if c == q: q = None
            elif c == "\\" and q == '"' and i + 1 < len(cmd): cur.append(cmd[i + 1]); i += 1
        elif c in "'\"":
            q = c; cur.append(c)
        elif c == "\\" and i + 1 < len(cmd):
            cur.append(c); cur.append(cmd[i + 1]); i += 1
        elif c in ";&|\n":
            parts.append("".join(cur)); cur = []
        else:
            cur.append(c)
        i += 1
    parts.append("".join(cur))
    return [p_.strip() for p_ in parts if p_.strip()]


def _segments(cmd):
    """Split a shell command line into simple commands, unwrapping `sh -c '...'`, `bash -lc`, `env X=1 cmd`, `nohup`, `xargs`."""
    out = []
    for part in _split_unquoted(cmd):
        try: toks = shlex.split(part, comments=False)
        except ValueError: toks = part.split()
        while toks and (re.fullmatch(r"\w+=\S*", toks[0]) or toks[0] in ("env", "sudo", "time", "nohup", "command", "exec", "xargs")):
            toks = toks[1:]
        if toks and os.path.basename(toks[0]) in ("sh", "bash", "zsh", "dash"):
            ci = next((i for i, t in enumerate(toks[1:], 1) if re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", t)), None)      # -c, -lc, -ec ...
            if ci is not None and ci + 1 < len(toks): out += _segments(toks[ci + 1]); continue
        if toks: out.append(toks)
    return out


def _is_python(tok): return bool(re.fullmatch(r"python[\d.]*", os.path.basename(tok)))


def check_segment(toks, branch=None):
    head = os.path.basename(toks[0])
    joined = " ".join(toks)
    # paid TTS: python ... voice.py ... --confirm (not through orbital.py)
    if _is_python(head) and any(os.path.basename(t) == "voice.py" for t in toks) and "--confirm" in toks and not any(t.endswith("orbital.py") for t in toks):
        return "paid TTS must go through orbital.py (owner approval + budget + cache). A direct voice.py --confirm is blocked."
    if head in ("youtubeuploader", "youtube-upload", "youtube-uploader", "yt-upload", "gdrive-youtube"):
        return "publishing to YouTube is the owner's decision; prepare the package instead."
    if head in ("curl", "wget", "http", "https", "xh") or (_is_python(head) and ("-c" in toks)):
        if PAID_API.search(joined):
            return "calling the ElevenLabs generation endpoints directly is blocked: paid requests go through orbital.py."
        if YOUTUBE_UP.search(joined):
            return "publishing to YouTube is the owner's decision; prepare the package instead."
    if head == "git":
        rest = toks[1:]
        while rest and (rest[0].startswith("-") or rest[0] in (".",)):          # git -C dir, git -c k=v ...
            rest = rest[2:] if rest[0] in ("-C", "-c") else rest[1:]
        sub = rest[0] if rest else ""
        args = rest[1:]
        if sub == "push":
            if any(a in ("--mirror", "--all", "--tags") for a in args) and False: pass
            if any(a == "--mirror" for a in args): return "git push --mirror is blocked."
            force = any(a in ("-f", "--force", "--force-with-lease") or a.startswith("--force-with-lease=") or (a.startswith("+") and len(a) > 1) for a in args)
            targets = [a for a in args if not a.startswith("-")]
            refspecs = targets[1:] if len(targets) > 1 else []
            for r in refspecs:
                dst = r.split(":")[-1].lstrip("+")
                if re.fullmatch(MAIN, dst): return "pushing to main is blocked; push your branch and open a PR."
            if any(a == "--all" for a in args): return "git push --all would include main; push your branch by name."
            if force and any(re.fullmatch(MAIN, r.split(":")[-1].lstrip("+")) for r in refspecs): return "force push to main is blocked."
            b = branch or current_branch()
            if len(targets) <= 1 and b in ("main", "master"): return "you are on main; switch to a branch before pushing."
            if len(targets) <= 1 and force and b in ("main", "master"): return "force push on main is blocked."
        if sub in ("commit", "merge", "cherry-pick", "rebase", "reset", "revert", "am") and (branch or current_branch()) in ("main", "master"):
            return "never change main; create a branch first."
        if sub in ("checkout", "restore", "rm", "mv", "clean", "stash", "reset", "revert") and PROTECTED.search(joined):
            return "this git command would modify a finished EP001/EP002 deliverable."
    inplace = re.compile(r"-[a-zA-Z]*i[a-zA-Z.]*$")
    if head in ("sed", "perl", "ruby", "awk") and any(inplace.fullmatch(t) or t == "--in-place" for t in toks[1:]):
        if PROTECTED.search(joined): return "finished EP001/EP002 deliverables are read-only (in-place edit)."
    if head in WRITERS:
        paths = [t for t in toks[1:] if not t.startswith("-")]
        if head in ("cp", "install", "rsync", "ln"):                     # only the destination changes
            hit = bool(paths) and bool(PROTECTED.search(" " + paths[-1]))
        else:                                                             # rm, mv (moves the source away), tee, truncate, dd ...
            hit = bool(PROTECTED.search(joined))
        if hit: return "finished EP001/EP002 deliverables are read-only (write a new file elsewhere)."
    return None


def check_bash(cmd, branch=None):
    for m in re.finditer(r">>?\s*(\S+)", cmd):                               # shell redirects into protected files
        if PROTECTED.search(m.group(1).strip("'\"")): return "finished EP001/EP002 deliverables are read-only (redirect blocked)."
    if re.search(r"\b(curl|wget|urllib|requests|http\.client|httpx|aiohttp|fetch|node|deno)\b", cmd):     # the quoting of a python -c / node -e body defeats tokenising
        if PAID_API.search(cmd): return "calling the ElevenLabs generation endpoints directly is blocked: paid requests go through orbital.py."
        if YOUTUBE_UP.search(cmd): return "publishing to YouTube is the owner's decision; prepare the package instead."
    for toks in _segments(cmd):
        msg = check_segment(toks, branch)
        if msg: return msg
    return None


def check_edit(path, content="", exists=None):
    p = path.replace("\\", "/")
    if PROTECTED.search(p):
        return f"{path} is a finished EP001/EP002 deliverable - do not modify it (write a new file elsewhere)."
    if content and SECRET.search(content):
        return "refusing to write what looks like an API key or token into a file."
    if content and PAID_API.search(content) and "/.claude/skills/yt-voice/" not in "/" + p and "/tools/autopilot/" not in "/" + p \
            and not p.endswith((".md", ".json", ".txt")):
        return "a new script that calls the paid generation API is blocked; paid requests go through yt-voice + orbital.py (approval gate)."
    if content and p.endswith((".py", ".js", ".mjs")) and CODE_DIRS.search("/" + p) and not re.search(r"(^|/)(test_[^/]*|[^/]*_test|conftest)\.py$", p):
        if exists is None: exists = os.path.exists(path)
        if not exists:
            try:
                import effects
                hits = effects.reuse_check(path, content)
            except Exception:
                hits = []
            if hits:
                h = hits[0]
                return (f"a similar effect already exists: '{h['id']}' ({h['status']}) - {h['what']} See knowledge/effects.json / `python3 tools/memory/effects.py search WORDS` "
                        f"and reuse it. If this really is different, put `# {effects.MARKER} <why it differs>` in the file.")
    return None


def check_mcp(tool, inp):
    name = tool.split("__")[-1]
    if tool.startswith("mcp__github__"):
        if name in ("merge_pull_request", "enable_pr_auto_merge"):
            return "merging is the owner's decision (the audit order is #17 first, then #18); do not merge or enable auto-merge."
        if name in ("push_files", "create_or_update_file", "delete_file"):
            br = str(inp.get("branch", "")).replace("refs/heads/", "")
            if br in ("main", "master", ""): return "writing to main (or to the default branch) through the GitHub tools is blocked; use a branch."
            if any(PROTECTED.search(str(f.get("path", ""))) for f in (inp.get("files") or []) if isinstance(f, dict)) or PROTECTED.search(str(inp.get("path", ""))):
                return "finished EP001/EP002 deliverables are read-only."
        if name == "update_pull_request" and str(inp.get("base", "")) in ("main", "master") and False: pass
    if "youtube" in tool.lower() and re.search(r"upload|insert|publish", name, re.I):
        return "publishing to YouTube is the owner's decision."
    return None


def decide(call, branch=None):
    tool, inp = call.get("tool_name", ""), call.get("tool_input", {}) or {}
    if tool == "Bash": return check_bash(inp.get("command", ""), branch)
    if tool in ("Edit", "Write", "MultiEdit"):
        content = inp.get("content", "") or inp.get("new_string", "") or "".join(e.get("new_string", "") for e in inp.get("edits", []) if isinstance(e, dict))
        return check_edit(inp.get("file_path", ""), content, exists=(tool != "Write") or None)
    if tool.startswith("mcp__"): return check_mcp(tool, inp)
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
