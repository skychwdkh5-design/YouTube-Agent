#!/usr/bin/env python3
"""recover_ep001_stacks.py - rebuild the EP001 TOA-reflectance stacks (EO, TW, TE) from the restored source bands and prove them against the
reports stored in the repository. Free, local, never touches the finished EP001 files (everything is written to a scratch directory).

    python3 tools/autopilot/recover_ep001_stacks.py --tree DIR --workspace DIR --out DIR [--stacks EO TW TE]

--tree       a checkout of production/ep001-sahara-green (git archive is enough): provides landsat/source_bands/{scripts/process.py, reports/*.json}
--workspace  the source bands restored with landsat/source_bands/scripts/restore_source_bands.py (78 files, SHA-512 verified there)
--out        new scratch directory; process.py is copied here with its hard-coded scratch paths pointed at --workspace/--out (the repo copy is untouched)
process.py needs a grid.json per stack; it is rebuilt from the stored report (grid x0 +15 m, y_top -15 m, the half-pixel snap process.py undoes).
Result: for each stack `identical` is True only when the rebuilt report (valid fractions, medians, registration shifts, stretch, cloud fractions) equals the
stored one exactly. This proves the first link of the chain (source bands -> reflectance); it does NOT prove the final video (see docs/production-knowledge)."""
import argparse, json, os, re, subprocess, sys

GRID_DIR = {"EO": "prev_eo", "TW": "prev_toshkaW", "TE": "prev_toshkaE"}


def grid_from_report(rep):
    g = {k: rep["grid"][k] for k in ("epsg", "x0", "y_top", "pixel_m", "width", "height")}
    g["x0"] += 15.0; g["y_top"] -= 15.0
    return g


def patch_process(src, scratch, workspace):
    """Point the three hard-coded paths of process.py at the new directories. Fails loudly when the script has another layout."""
    out, n = re.subn(r"(?m)^S = .*$", f"S = {scratch!r}", src)
    out, m = re.subn(r"(?m)^W = .*$", f"W = {workspace!r}", out)
    out, k = re.subn(r"(?m)^OUT = .*$", "OUT = S + '/out'; os.makedirs(OUT, exist_ok=True)", out)
    if (n, m, k) != (1, 1, 1): raise ValueError(f"process.py layout not recognised (S/W/OUT matches: {n}/{m}/{k})")
    return out


def compare(stored, rebuilt):
    return {"identical": stored == rebuilt, "differing_keys": sorted(k for k in set(stored) | set(rebuilt) if stored.get(k) != rebuilt.get(k))}


def run(tree, workspace, out, stacks=("EO", "TW", "TE")):
    sb = os.path.join(tree, "productions", "sahara-green", "landsat", "source_bands")
    if os.path.exists(out) and os.listdir(out): raise ValueError(f"{out} must be new or empty (nothing is overwritten)")
    os.makedirs(os.path.join(out, "scripts"), exist_ok=True)
    script = os.path.join(out, "scripts", "process.py")
    with open(os.path.join(sb, "scripts", "process.py"), encoding="utf-8") as f: src = f.read()
    with open(script, "w", encoding="utf-8") as f: f.write(patch_process(src, out, workspace))
    result = {}
    for st in stacks:
        stored = json.load(open(os.path.join(sb, "reports", f"{st}_report.json")))
        gd = os.path.join(workspace, GRID_DIR[st]); os.makedirs(gd, exist_ok=True)
        json.dump(grid_from_report(stored), open(os.path.join(gd, "grid.json"), "w"))
        r = subprocess.run([sys.executable, "-I", script, st], capture_output=True, text=True)
        if r.returncode != 0:
            result[st] = {"identical": False, "error": (r.stdout + r.stderr)[-300:]}; continue
        result[st] = compare(stored, json.load(open(os.path.join(out, "out", f"{st}_report.json"))))
        print(st, "identical" if result[st]["identical"] else f"DIFFERS {result[st]['differing_keys']}", flush=True)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tree", required=True); ap.add_argument("--workspace", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--stacks", nargs="*", default=["EO", "TW", "TE"])
    a = ap.parse_args(argv)
    try: res = run(a.tree, a.workspace, a.out, a.stacks)
    except (ValueError, OSError, KeyError) as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})); return 2
    ok = all(v.get("identical") for v in res.values())
    print(json.dumps({"ok": ok, "stacks": res}, indent=1)); return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
