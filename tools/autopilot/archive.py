#!/usr/bin/env python3
"""archive.py - preserve a finished episode so that losing the container loses nothing paid or finished.

    python3 tools/autopilot/archive.py create SLUG --out DIR [--part-bytes 94371840] [--with-cache]
    python3 tools/autopilot/archive.py verify DIR
    python3 tools/autopilot/archive.py restore DIR --to DEST [--only NAME]
    python3 tools/autopilot/archive.py recoverable SLUG          # can the paid narration be rebuilt from the saved responses?

`create` copies the episode's irreplaceable and release files into a NEW directory laid out for a `media/<slug>-final`
(or `-audio`) branch: files over --part-bytes (90 MiB; GitHub rejects 100 MB) are split into `<name>.partNN`, every file and
every part gets a SHA-256 in `SHA256SUMS` (sha256sum format) and `ARCHIVE_MANIFEST.json` (role, size, parts, hash of the JOINED
file). `verify` re-hashes everything - including the joined hash of split files, streamed, without writing the big file -
and exits 1 on any mismatch or missing part. `restore` joins parts into DEST (never overwrites) and re-checks the hash.
Nothing here pushes, uploads or deletes. Pushing the result to a media/* branch is a separate, ordinary git push (never main);
Git LFS is an alternative for a single file but needs the LFS hosts allowed (docs/production-knowledge/RENDERING.md).

Roles, in order of what cannot be regenerated: `paid` (narration cache + .voice.json - the ElevenLabs responses), `master`
(final MP4), `release` (package, captions, thumbnail), `build` (timeline, graphics specs, QC JSON). Rendered media is large
and re-renderable; the paid responses are small and are not. --with-cache includes voice/cache (usually ~12 MB).
"""
import hashlib, json, os, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_PART = 90 * 1024 * 1024
BUF = 1 << 20


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(BUF), b""): h.update(b)
    return h.hexdigest()


def sha256_parts(paths):
    h = hashlib.sha256()
    for p in paths:
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(BUF), b""): h.update(b)
    return h.hexdigest()


# role -> (relative path or glob root, recursive?)
PLAN = [("paid", "voice/narration.voice.json"), ("paid", "voice/narration.wav"), ("paid", "voice/tts_plan.json"), ("paid", "ledger.json"),
        ("master", "final.mp4"), ("release", "release"), ("release", "captions"), ("build", "timeline.json"), ("build", "grid.json"),
        ("build", "story"), ("build", "qc"), ("build", "approvals.json"), ("build", "state.json"), ("build", "graphics"), ("build", "assets/manifest.json")]


def collect(prod, with_cache):
    items = list(PLAN) + ([("paid", "voice/cache")] if with_cache else [])
    out = []
    for role, rel in items:
        p = os.path.join(prod, rel)
        if os.path.isfile(p): out.append((role, rel))
        elif os.path.isdir(p):
            for dp, _, fns in os.walk(p):
                for fn in sorted(fns):
                    full = os.path.join(dp, fn)
                    out.append((role, os.path.relpath(full, prod)))
    return sorted(set(out), key=lambda x: (["paid", "master", "release", "build"].index(x[0]), x[1]))


def create(prod, out_dir, part_bytes=DEFAULT_PART, with_cache=False):
    if os.path.exists(out_dir) and os.listdir(out_dir): raise ValueError(f"{out_dir} is not empty; an archive is never written over existing files")
    os.makedirs(out_dir, exist_ok=True)
    files, sums = [], []
    for role, rel in collect(prod, with_cache):
        src = os.path.join(prod, rel)
        size = os.path.getsize(src)
        dst = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        entry = {"path": rel, "role": role, "bytes": size, "sha256": sha256_file(src)}
        if size > part_bytes:
            parts = []
            with open(src, "rb") as f:
                n = 0
                while True:
                    chunk = f.read(part_bytes)
                    if not chunk: break
                    pn = f"{rel}.part{n:02d}"
                    with open(os.path.join(out_dir, pn), "wb") as g: g.write(chunk)
                    parts.append({"path": pn, "bytes": len(chunk), "sha256": hashlib.sha256(chunk).hexdigest()})
                    sums.append((parts[-1]["sha256"], pn)); n += 1
            entry["parts"] = parts
        else:
            shutil.copyfile(src, dst)
            sums.append((entry["sha256"], rel))
        files.append(entry)
        if "parts" in entry: sums.append((entry["sha256"], rel + "  (joined)"))
    manifest = {"schema": "orbitalatlas-archive/1", "slug": os.path.basename(os.path.normpath(prod)), "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "part_bytes": part_bytes, "files": files,
                "restore": "python3 tools/autopilot/archive.py restore <this dir> --to <new dir>   (joins parts, verifies SHA-256, never overwrites)",
                "join_by_hand": "cat FILE.part* > FILE   then   sha256sum FILE   and compare with ARCHIVE_MANIFEST.json"}
    with open(os.path.join(out_dir, "ARCHIVE_MANIFEST.json"), "w", encoding="utf-8") as f: json.dump(manifest, f, indent=1)
    with open(os.path.join(out_dir, "SHA256SUMS"), "w", encoding="utf-8") as f:
        for h, n in sums:
            if not n.endswith("(joined)"): f.write(f"{h}  {n}\n")
    return {"ok": True, "out": out_dir, "files": len(files), "split": sum(1 for e in files if "parts" in e), "bytes": sum(e["bytes"] for e in files)}


def verify(arch):
    with open(os.path.join(arch, "ARCHIVE_MANIFEST.json"), encoding="utf-8") as f: m = json.load(f)
    problems, checked = [], 0
    for e in m["files"]:
        if "parts" in e:
            paths = []
            for p in e["parts"]:
                full = os.path.join(arch, p["path"])
                if not os.path.exists(full): problems.append(f"missing part {p['path']}"); continue
                if sha256_file(full) != p["sha256"]: problems.append(f"part hash mismatch {p['path']}")
                paths.append(full); checked += 1
            if len(paths) == len(e["parts"]) and sha256_parts(paths) != e["sha256"]: problems.append(f"joined hash mismatch {e['path']}")
        else:
            full = os.path.join(arch, e["path"])
            if not os.path.exists(full): problems.append(f"missing file {e['path']}"); continue
            if sha256_file(full) != e["sha256"]: problems.append(f"hash mismatch {e['path']}")
            checked += 1
    sums = os.path.join(arch, "SHA256SUMS")
    if os.path.exists(sums):                                  # the plain sha256sum file must agree too
        with open(sums, encoding="utf-8") as f:
            for line in f:
                h, _, n = line.strip().partition("  ")
                full = os.path.join(arch, n)
                if os.path.exists(full) and sha256_file(full) != h: problems.append(f"SHA256SUMS mismatch {n}")
    return {"ok": not problems, "files_in_manifest": len(m["files"]), "objects_checked": checked, "problems": problems}


def restore(arch, dest, only=None):
    v = verify(arch)
    if not v["ok"]: raise ValueError("the archive does not verify: " + "; ".join(v["problems"][:3]))
    with open(os.path.join(arch, "ARCHIVE_MANIFEST.json"), encoding="utf-8") as f: m = json.load(f)
    if os.path.exists(dest) and os.listdir(dest): raise ValueError(f"{dest} is not empty; restore never overwrites")
    os.makedirs(dest, exist_ok=True)
    done = []
    for e in m["files"]:
        if only and e["path"] != only: continue
        out = os.path.join(dest, e["path"]); os.makedirs(os.path.dirname(out), exist_ok=True)
        if "parts" in e:
            with open(out, "wb") as g:
                for p in e["parts"]:
                    with open(os.path.join(arch, p["path"]), "rb") as f: shutil.copyfileobj(f, g, BUF)
        else:
            shutil.copyfile(os.path.join(arch, e["path"]), out)
        if sha256_file(out) != e["sha256"]: raise ValueError(f"restored file does not match its recorded hash: {e['path']}")
        done.append(e["path"])
    return {"ok": True, "restored": len(done), "dest": dest}


def recoverable(prod):
    """Can the paid narration be rebuilt without paying again?"""
    meta = os.path.join(prod, "voice", "narration.voice.json")
    cache = os.path.join(prod, "voice", "cache")
    out = {"voice_json": os.path.exists(meta), "cache_dir": os.path.isdir(cache) and len(os.listdir(cache)) > 0,
           "wav_present": os.path.exists(os.path.join(prod, "voice", "narration.wav"))}
    out["recoverable_without_paying"] = out["wav_present"] or (out["voice_json"] and out["cache_dir"])
    out["how"] = ("narration.wav is present" if out["wav_present"] else
                  "python3 tools/autopilot/recover_narration.py --meta voice/narration.voice.json --cache voice/cache --out NEW_DIR (byte-identical proof)" if out["recoverable_without_paying"] else
                  "NOT recoverable: no cache and no WAV - the narration would have to be paid again (needs the owner's approval)")
    return out


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 2 or a[0] not in ("create", "verify", "restore", "recoverable"):
        print(__doc__); return 2
    def opt(n, d=None): return a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else d
    prods = os.environ.get("ORBITAL_PRODUCTIONS") or os.path.join(ROOT, "productions")
    try:
        if a[0] == "create": r = create(os.path.join(prods, a[1]), opt("--out"), int(opt("--part-bytes", DEFAULT_PART)), "--with-cache" in a)
        elif a[0] == "verify": r = verify(a[1])
        elif a[0] == "restore": r = restore(a[1], opt("--to"), opt("--only"))
        else: r = recoverable(os.path.join(prods, a[1]))
    except (ValueError, OSError, KeyError) as x:
        print(json.dumps({"ok": False, "error": f"{type(x).__name__}: {x}"})); return 2
    print(json.dumps(r, indent=1)); return 0 if r.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
