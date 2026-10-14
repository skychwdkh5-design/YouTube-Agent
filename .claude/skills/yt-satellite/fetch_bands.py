#!/usr/bin/env python3
"""Bounded, resumable download of Landsat Level-1 band files for many scenes (wraps usgs_m2m.py download-bands).

Why it exists: USGS answers some download requests with HTTP 504 / timeouts. A single try loses the tile; an unbounded wait hides it.
Rules implemented here (tests: test_fetch_bands.py):
  * a tile whose bands + MTL already exist is never requested again;
  * every attempt has a hard wall-clock limit (the child process is killed), at most `attempts` tries, exponential back-off;
  * only transient failures (504/502/503/429, timeouts, 'not ready', connection errors) are retried; permanent ones (no download option,
    --max-mb exceeded, authentication, bad arguments) stop at once;
  * the result is a JSON report per tile; exit code 0 only when every tile is complete.
Spec file: {"out_dir": "...", "tiles": [{"dataset": "landsat_ot_c2_l1", "bands": "B4,B3,B2", "entity": "LC9...", "display_id": "LC09_..."}]}
Usage: fetch_bands.py SPEC.json [--attempts 4] [--per-attempt-s 900] [--confirm]   (--confirm is the USGS download confirmation of usgs_m2m)
Progress is printed per tile and attempt. Never use `pgrep -f NAME` to wait for it (see tools/autopilot/procs.py)."""
import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
M2M = os.path.join(HERE, "usgs_m2m.py")
TRANSIENT = ("504", "502", "503", "429", "gateway", "time-out", "timed out", "timeout", "not ready", "temporarily", "connection reset",
             "connection aborted", "remote end closed", "urlerror", "no download url")
PERMANENT = ("no_options", "no band-file download option", "exceeded --max-mb", "unauthor", "authentication", "invalid", "forbidden", "401", "403")


def band_names(bands): return [b.strip() for b in bands.split(",") if b.strip()]


def complete(display_id, bands, out_dir):
    need = [f"{display_id}_{b}.TIF" for b in band_names(bands)] + [f"{display_id}_MTL.txt"]
    return all(os.path.isfile(os.path.join(out_dir, n)) and os.path.getsize(os.path.join(out_dir, n)) > 0 for n in need)


def classify(error):
    """'transient' | 'permanent' | 'unknown' (unknown is retried once less aggressively: treated as transient by the caller)."""
    e = (error or "").lower()
    if any(p in e for p in PERMANENT): return "permanent"
    if any(t in e for t in TRANSIENT): return "transient"
    return "unknown"


def run_download(tile, out_dir, per_attempt_s, confirm=True):
    """One child process with a hard time limit. Returns the parsed JSON of usgs_m2m, or {'status':'error','error':...}."""
    cmd = [sys.executable, M2M, "download-bands", "--dataset", tile["dataset"], "--entity", tile["entity"], "--display-id", tile["display_id"],
           "--bands", tile["bands"], "--out", out_dir] + (["--confirm"] if confirm else [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=per_attempt_s)
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": f"timed out: attempt exceeded {per_attempt_s}s and was killed"}
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"status": "error", "error": (r.stdout + r.stderr)[-300:] or f"exit {r.returncode}"}


def fetch_tile(tile, out_dir, attempts=4, per_attempt_s=900, runner=run_download, sleep=time.sleep, log=print, base_wait=30, max_wait=240):
    did = tile["display_id"]
    if complete(did, tile["bands"], out_dir):
        log(f"{did}: already complete, skipped")
        return {"display_id": did, "status": "skipped_complete", "attempts": 0}
    last = ""
    for a in range(1, attempts + 1):
        t0 = time.time()
        j = runner(tile, out_dir, per_attempt_s)
        ok = j.get("status") == "ok" and complete(did, tile["bands"], out_dir)
        last = j.get("error") or ("" if ok else "reported ok but files are missing")
        log(f"{did}: attempt {a}/{attempts} {'ok' if ok else 'FAILED'} in {time.time() - t0:.0f}s {last}".rstrip())
        if ok: return {"display_id": did, "status": "ok", "attempts": a}
        kind = classify(last)
        if kind == "permanent":
            return {"display_id": did, "status": "failed_permanent", "attempts": a, "error": last}
        if a < attempts: sleep(min(max_wait, base_wait * 2 ** (a - 1)))
    return {"display_id": did, "status": "failed_gave_up", "attempts": attempts, "error": last}


def fetch_all(spec, attempts=4, per_attempt_s=900, **kw):
    out_dir = spec["out_dir"]; os.makedirs(out_dir, exist_ok=True)
    res = []
    for i, t in enumerate(spec["tiles"], 1):
        kw.get("log", print)(f"[{i}/{len(spec['tiles'])}] {t['display_id']}")
        res.append(fetch_tile(t, out_dir, attempts, per_attempt_s, **kw))
    ok = all(r["status"] in ("ok", "skipped_complete") for r in res)
    return {"ok": ok, "tiles": res, "complete": sum(r["status"] in ("ok", "skipped_complete") for r in res), "total": len(res)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec"); ap.add_argument("--attempts", type=int, default=4); ap.add_argument("--per-attempt-s", type=int, default=900)
    ap.add_argument("--confirm", action="store_true", help="required: confirms the (free) USGS download")
    a = ap.parse_args(argv)
    if not a.confirm:
        print(json.dumps({"status": "error", "error": "pass --confirm to download"})); return 2
    spec = json.load(open(a.spec))
    rep = fetch_all(spec, a.attempts, a.per_attempt_s)
    print(json.dumps(rep, indent=1)); return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
