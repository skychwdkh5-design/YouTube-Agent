#!/usr/bin/env python3
"""protected.py - proof that the finished EP001/EP002 deliverables were not touched.

    python3 tools/autopilot/protected.py verify [--head REF]

For every reference branch in protected.json that exists in this clone, every file under the protected paths must be
byte-identical in HEAD (same git blob) - or absent from HEAD's history altogether (a branch that never contained the
release). A modified file, or a deleted file inside a directory HEAD does contain, is a violation. This is the check that
does not depend on which tool, script or command did the writing. Exit code 1 on any violation.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _git(root, *a):
    return subprocess.run(["git", "-C", root, *a], capture_output=True, text=True)


def load_config(path=None):
    with open(path or os.path.join(HERE, "protected.json"), encoding="utf-8") as f: return json.load(f)


def verify(root=ROOT, head="HEAD", config=None):
    cfg = config or load_config()
    violations, checked, skipped = [], 0, []
    for ref in cfg["release_refs"]:
        if _git(root, "rev-parse", "--verify", "-q", ref + "^{commit}").returncode != 0:
            skipped.append(ref); continue
        for path in cfg["paths"]:
            ls = _git(root, "ls-tree", "-r", ref, "--", path)
            for line in ls.stdout.splitlines():
                meta, name = line.split("\t", 1)
                blob = meta.split()[2]
                cur = _git(root, "rev-parse", "--verify", "-q", f"{head}:{name}")
                if cur.returncode != 0:
                    if _git(root, "cat-file", "-e", f"{head}:{path.rstrip('/')}").returncode == 0:   # HEAD has the directory but not this file
                        violations.append({"file": name, "ref": ref, "problem": "deleted"})
                    continue
                checked += 1
                if cur.stdout.strip() != blob:
                    violations.append({"file": name, "ref": ref, "problem": "modified"})
    return {"ok": not violations, "checked_files": checked, "violations": violations, "refs_not_in_this_clone": skipped}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] != "verify":
        print(__doc__); return 2
    head = a[a.index("--head") + 1] if "--head" in a else "HEAD"
    r = verify(head=head)
    print(json.dumps(r, indent=1))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
