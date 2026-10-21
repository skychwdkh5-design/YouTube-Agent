#!/usr/bin/env python3
"""media_cache.py - a shared cache of already VERIFIED media (rights evidence, author, licence, credit, sha256, the file itself) and of the provider probe, so the same photo or the same
source check is never done twice, and one automatic pass per episode: probe -> search -> verify -> fetch -> exceptions.

    python3 media_cache.py auto --root productions/<slug>          # needs research/notes.json "media_scenes": {"<chapter>": ["query", ...]}
    python3 media_cache.py put  --root productions/<slug> --id <ledger id>      # file a VERIFIED entry into the cache
    python3 media_cache.py apply --root productions/<slug>          # fill ledger entries from the cache (offline)

The cache lives in media_cache/ at the repo root (index.json is small and committed; media_cache/assets is git-ignored). Nothing is ever marked VERIFIED here that media.py's own
evaluate() would not verify; an item without confirmed rights is simply not used. A chapter with no VERIFIED real photo/video is written to media/exceptions.json
(a visible exception to the visual standard, never hidden).
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CACHE = os.path.join(REPO, "media_cache")
sys.path.insert(0, HERE)
import media as M

PROBE_TTL_S = 24 * 3600
KEYS = ("title", "author", "license", "kind", "page_url", "file_url", "license_url", "attribution_text", "rights_evidence", "on_screen_label", "date", "depicts_reality", "rights_class", "sha256", "retrieved")


def _index():
    p = os.path.join(CACHE, "index.json")
    return json.load(open(p)) if os.path.exists(p) else {"schema": "yt-media-cache/1", "entries": {}, "probe": None}


def _save(ix):
    os.makedirs(CACHE, exist_ok=True)
    tmp = os.path.join(CACHE, "index.json.part")
    json.dump(ix, open(tmp, "w"), indent=1, ensure_ascii=False)
    os.replace(tmp, os.path.join(CACHE, "index.json"))


def lookup(page_url):
    return _index()["entries"].get(page_url)


def put(entry, root):
    """File a VERIFIED ledger entry (and its file) into the cache."""
    if entry.get("status") != "VERIFIED":
        raise ValueError("only VERIFIED entries are cached")
    src = os.path.join(root, entry["local_path"])
    if hashlib.sha256(open(src, "rb").read()).hexdigest() != entry["sha256"]:
        raise ValueError("file does not match its recorded sha256")
    os.makedirs(os.path.join(CACHE, "assets"), exist_ok=True)
    dst = os.path.join(CACHE, "assets", entry["sha256"][:16] + os.path.splitext(src)[1])
    if not os.path.exists(dst):
        shutil.copyfile(src, dst)
    ix = _index()
    ix["entries"][entry["page_url"]] = dict({k: entry.get(k) for k in KEYS}, cached_file=os.path.relpath(dst, CACHE), verified_on=time.strftime("%Y-%m-%d"))
    _save(ix)
    return ix["entries"][entry["page_url"]]


def apply(root):
    """Offline: ledger entries that are not VERIFIED but whose page is in the cache take the cached rights and file (the sha256 is re-checked)."""
    led = M.load(root); ix = _index(); n = 0
    for e in led["entries"]:
        c = ix["entries"].get(e.get("page_url"))
        if not c or e.get("status") == "VERIFIED" or e.get("rejected_by_owner"):
            continue
        f = os.path.join(CACHE, c["cached_file"])
        if not os.path.exists(f) or hashlib.sha256(open(f, "rb").read()).hexdigest() != c["sha256"]:
            continue
        os.makedirs(os.path.join(root, "media", "assets"), exist_ok=True)
        lp = os.path.join("media", "assets", os.path.basename(f))
        shutil.copyfile(f, os.path.join(root, lp))
        e.update({k: c[k] for k in KEYS if c.get(k) is not None}, local_path=lp)
        n += 1
    M.refresh(led, root); M.save(root, led)
    return n


def probe_cached():
    ix = _index()
    p = ix.get("probe")
    if p and time.time() - p["at"] < PROBE_TTL_S:
        return p["result"], True
    res = M.probe()
    ix["probe"] = {"at": time.time(), "result": res}; _save(ix)
    return res, False


def auto(root, run=subprocess.run):
    """One automatic pass for an episode. Returns a short summary dict; writes media/exceptions.json."""
    notes = json.load(open(os.path.join(root, "research", "notes.json")))
    scenes = notes.get("media_scenes") or {}
    t0 = time.time()
    summary = {"cached_applied": apply(root) if os.path.exists(M.ledger_path(root)) else 0, "searched": 0, "usable_providers": []}
    probe, cached = probe_cached()
    usable = [p["source"] for p in probe if p.get("usable") and p.get("status") == "OK"]          # manual sources (usgs, press pages) cannot be searched automatically
    summary.update(usable_providers=usable, probe_from_cache=cached)
    for ch, qs in scenes.items():
        for q in qs:
            if usable:
                run([sys.executable, os.path.join(HERE, "media.py"), "search", "--root", root, "--scene", ch, "--query", q, "--sources", ",".join(usable)], capture_output=True, text=True)
                summary["searched"] += 1
    if os.path.exists(M.ledger_path(root)):
        run([sys.executable, os.path.join(HERE, "media.py"), "verify", "--root", root], capture_output=True, text=True)
        run([sys.executable, os.path.join(HERE, "media.py"), "fetch", "--root", root, "--confirm"], capture_output=True, text=True)
    led = M.load(root) if os.path.exists(M.ledger_path(root)) else {"entries": []}
    ok = {e["scene"] for e in led["entries"] if e.get("status") == "VERIFIED" and e.get("kind") in ("photo", "video") and e.get("depicts_reality", True)}
    exc = [{"chapter": ch, "reason": ("no provider reachable from this machine (see media.py probe)" if not usable else "no verified free real photo or video found for the queries"), "queries": qs}
           for ch, qs in scenes.items() if ch not in ok]
    os.makedirs(os.path.join(root, "media"), exist_ok=True)
    json.dump({"schema": "yt-media-exceptions/1", "note": "chapters that fall outside the real-photo/video standard; shown to the owner, never hidden", "exceptions": exc}, open(os.path.join(root, "media", "exceptions.json"), "w"), indent=1)
    for e in led["entries"]:
        if e.get("status") == "VERIFIED" and e.get("sha256") and e.get("local_path"):
            try:
                put(e, root)
            except (ValueError, OSError):
                pass
    summary.update(verified_scenes=sorted(ok), exceptions=[x["chapter"] for x in exc], seconds=round(time.time() - t0, 1))
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("auto", "put", "apply"):
        p = sub.add_parser(n); p.add_argument("--root", required=True)
        if n == "put":
            p.add_argument("--id", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "auto":
        print(json.dumps(auto(a.root)))
    elif a.cmd == "apply":
        print(json.dumps({"applied": apply(a.root)}))
    else:
        e = next(x for x in M.load(a.root)["entries"] if x["id"] == a.id)
        print(json.dumps(put(e, a.root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
