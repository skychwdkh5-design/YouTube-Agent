#!/usr/bin/env python3
"""media.py - keep approved MP4s in a DRAFT GitHub Release and fetch them back with checksum checks.

    python3 media.py stage --manifest publish/media.json     # Git LFS branch -> draft release (skips what is already there)
    python3 media.py fetch --manifest publish/media.json --dest media [--names a.mp4,b.mp4]
    python3 media.py verify --manifest publish/media.json    # compare release assets with the manifest, downloads nothing

Why a DRAFT release: the repo is public. Draft releases and their assets are visible only to people with
write access, and release downloads do not use the Git LFS bandwidth quota. Needs GITHUB_TOKEN and
GITHUB_REPOSITORY (both present in Actions; the workflow needs `contents: write`). Stdlib only.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, urllib.error, urllib.request

API = "https://api.github.com"
UA = "YouTube-Agent-media/1.0"


class MediaError(Exception):
    pass


def _req(method, url, data=None, headers=None, auth=True, timeout=120):
    h = {"User-Agent": UA, "Accept": "application/vnd.github+json", **(headers or {})}
    if auth:
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    return urllib.request.Request(url, data=data, method=method, headers=h)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def gh(method, path, body=None):
    repo = os.environ["GITHUB_REPOSITORY"]
    url = path if path.startswith("http") else f"{API}/repos/{repo}/{path}"
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(_req(method, url, data, {"Content-Type": "application/json"} if data else None), timeout=120) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise MediaError(f"GitHub API {e.code} on {method} {path.split('?')[0]}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def find_release(name):
    page = 1
    while True:
        rels = gh("GET", f"releases?per_page=100&page={page}")
        for r in rels:
            if r["name"] == name:
                return r
        if len(rels) < 100:
            return None
        page += 1


def ensure_release(name):
    r = find_release(name)
    if r:
        if not r["draft"]:
            raise MediaError(f"release '{name}' is PUBLISHED - refusing to put unapproved media in a public release")
        return r
    return gh("POST", "releases", {"tag_name": name, "name": name, "draft": True, "body": "Staged media for yt-publish. Keep as DRAFT."})


def asset_ok(a, size, sha):
    d = a.get("digest")
    return a["state"] == "uploaded" and a["size"] == size and (d is None or d == f"sha256:{sha}")


def upload_asset(rel, path, size):
    name = os.path.basename(path)
    url = f"https://uploads.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/releases/{rel['id']}/assets?name={name}"
    with open(path, "rb") as f:
        req = _req("POST", url, f, {"Content-Type": "video/mp4", "Content-Length": str(size)})
        try:
            urllib.request.urlopen(req, timeout=1800).read()
        except urllib.error.HTTPError as e:
            raise MediaError(f"upload of {name} failed ({e.code})")


def download_asset(a, dest, size, sha):
    """API download -> 302 to a signed URL; the token must NOT follow the redirect."""
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        opener.open(_req("GET", a["url"], None, {"Accept": "application/octet-stream"}), timeout=60)
        raise MediaError("expected a redirect for the asset download")
    except urllib.error.HTTPError as e:
        if e.code not in (301, 302, 303, 307):
            raise MediaError(f"asset download refused ({e.code})")
        loc = e.headers["Location"]
    tmp = dest + ".part"
    with urllib.request.urlopen(urllib.request.Request(loc, headers={"User-Agent": UA}), timeout=1800) as r, open(tmp, "wb") as out:
        shutil.copyfileobj(r, out, 1 << 20)
    if os.path.getsize(tmp) != size or sha256(tmp) != sha:
        os.remove(tmp)
        raise MediaError(f"{os.path.basename(dest)}: size/sha256 mismatch after download - not used")
    os.replace(tmp, dest)


def fetch_from_lfs(item):
    """Materialise one LFS file from its media branch without smudging the rest of the branch."""
    src, repo = item["source"], os.environ["GITHUB_REPOSITORY"]
    work = tempfile.mkdtemp(prefix="lfs-")
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    url = f"https://x-access-token:{os.environ['GITHUB_TOKEN']}@github.com/{repo}.git"
    run = lambda *c: subprocess.run(c, cwd=work, env=env, check=True, capture_output=True)
    try:
        run("git", "init", "-q"); run("git", "remote", "add", "origin", url)
        run("git", "fetch", "-q", "--depth", "1", "origin", src["branch"]); run("git", "checkout", "-q", "FETCH_HEAD")
        run("git", "lfs", "pull", "--include", src["path"])
    except subprocess.CalledProcessError as e:
        raise MediaError("git/LFS step failed: " + e.stderr.decode()[-200:].replace(os.environ["GITHUB_TOKEN"], "[REDACTED]"))
    return os.path.join(work, src["path"]), work


def cmd_stage(m):
    rel, res = ensure_release(m["bundle"]), []
    have = {a["name"]: a for a in rel["assets"]}
    for it in m["files"]:
        a = have.get(it["asset"])
        if a and asset_ok(a, it["size"], it["sha256"]):
            res.append({"asset": it["asset"], "status": "already staged"})
            continue
        if a:
            gh("DELETE", f"releases/assets/{a['id']}")      # broken or partial upload from an earlier run
        path, work = fetch_from_lfs(it)
        try:
            if os.path.getsize(path) != it["size"] or sha256(path) != it["sha256"]:
                raise MediaError(f"{it['asset']}: LFS content does not match the manifest (size/sha256) - not staged")
            upload_asset(rel, path, it["size"])
        finally:
            shutil.rmtree(work, ignore_errors=True)
        res.append({"asset": it["asset"], "status": "staged"})
    return {"bundle": m["bundle"], "draft": True, "files": res, **cmd_verify(m)}


def cmd_verify(m):
    rel = find_release(m["bundle"])
    if not rel:
        raise MediaError(f"release '{m['bundle']}' not found")
    have = {a["name"]: a for a in rel["assets"]}
    bad = [it["asset"] for it in m["files"] if it["asset"] not in have or not asset_ok(have[it["asset"]], it["size"], it["sha256"])]
    return {"release_is_draft": rel["draft"], "all_assets_match_manifest": not bad and rel["draft"], "bad": bad}


def cmd_fetch(m, dest, names):
    rel = find_release(m["bundle"])
    if not rel:
        raise MediaError(f"release '{m['bundle']}' not found - run stage-media first")
    os.makedirs(dest, exist_ok=True)
    have = {a["name"]: a for a in rel["assets"]}
    out = []
    for it in m["files"]:
        if names and it["asset"] not in names:
            continue
        a, p = have.get(it["asset"]), os.path.join(dest, it["asset"])
        if not a:
            raise MediaError(f"{it['asset']} is not in the release")
        if os.path.isfile(p) and os.path.getsize(p) == it["size"] and sha256(p) == it["sha256"]:
            out.append({"asset": it["asset"], "status": "cached"})
            continue
        download_asset(a, p, it["size"], it["sha256"])
        out.append({"asset": it["asset"], "status": "downloaded, sha256 ok"})
    return {"files": out}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["stage", "fetch", "verify"]); p.add_argument("--manifest", required=True)
    p.add_argument("--dest", default="media"); p.add_argument("--names", default="")
    a = p.parse_args(argv)
    try:
        m = json.load(open(a.manifest))
        out = {"stage": lambda: cmd_stage(m), "verify": lambda: cmd_verify(m),
               "fetch": lambda: cmd_fetch(m, a.dest, set(filter(None, a.names.split(","))))}[a.cmd]()
        print(json.dumps(out, indent=2))
        return 0 if out.get("all_assets_match_manifest", True) else 1
    except (MediaError, KeyError) as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
