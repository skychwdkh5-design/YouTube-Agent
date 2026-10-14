#!/usr/bin/env python3
"""Safe process checks. `pgrep -f NAME` matches the full command line of EVERY process, including the shell that is running the check:
`until ! pgrep -f fetch_bands; do sleep 20; done` therefore finds itself and never ends (EP003, 30+ min 'hang' that was no download at all).
Rules: match the script (argv[1] basename) of an interpreter process, never a substring of a shell command line; exclude this process and its
ancestors; wait with a deadline and a progress line, never unbounded. CLI: procs.py list NAME | wait NAME [--timeout S]"""
import os, sys, time

SHELLS = {"bash", "sh", "zsh", "dash", "fish"}
INTERPRETERS = ("python", "node", "bun", "ruby", "perl")


def _cmdline(pid):
    try:
        return open(f"/proc/{pid}/cmdline", "rb").read().decode("utf-8", "replace").split("\0")[:-1]
    except OSError:
        return []


def _ppid(pid):
    try:
        return int(open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[1])
    except (OSError, ValueError, IndexError):
        return 0


def ancestors(pid=None):
    pid = pid or os.getpid(); out = set()
    while pid > 1 and pid not in out:
        out.add(pid); pid = _ppid(pid)
    return out


def is_match(argv, name):
    """True for an interpreter running a script called `name` (with or without .py); False for shells and for processes that merely mention it."""
    if not argv: return False
    exe = os.path.basename(argv[0])
    if exe in SHELLS or not exe.startswith(INTERPRETERS): return False
    script = next((os.path.basename(x) for x in argv[1:] if not x.startswith("-")), "")
    return script in (name, name + ".py")


def find(name, exclude=None, proc_root="/proc"):
    ex = set(exclude if exclude is not None else ancestors())
    pids = []
    for d in os.listdir(proc_root):
        if d.isdigit() and int(d) not in ex and is_match(_cmdline(int(d)), name):
            pids.append(int(d))
    return sorted(pids)


def wait_gone(name, timeout=600, poll=5, log=print, finder=find, sleep=time.sleep, clock=time.time):
    """Wait until no process runs `name`. Bounded: returns False on timeout. Prints progress every poll."""
    t0 = clock()
    while True:
        pids = finder(name)
        if not pids: return True
        if clock() - t0 >= timeout:
            log(f"timeout after {timeout}s: still running {pids}"); return False
        log(f"waiting for {name}: pids {pids}, {clock() - t0:.0f}s of {timeout}s"); sleep(poll)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "list":
        print(find(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "wait":
        t = int(sys.argv[sys.argv.index("--timeout") + 1]) if "--timeout" in sys.argv else 600
        sys.exit(0 if wait_gone(sys.argv[2], t) else 1)
    else:
        print(__doc__); sys.exit(2)
