#!/usr/bin/env python3
"""voice_cache.py - final narration through yt-voice (ElevenLabs), cached by text + voice + parameters, with spend limits.

    python3 pipeline/voice_cache.py --channel oa --release oa-20261119-01 --script script.md --out-dir DIR            # plan, no cost
    python3 pipeline/voice_cache.py --channel oa --release oa-20261119-01 --script script.md --out-dir DIR --confirm  # paid, once

* The cache key is sha256 of (provider, voice id, model, voice settings, exact spoken text). A hit copies the cached files and
  costs nothing - so a re-run after a crash, a re-render or a new cover never pays twice for the same narration.
* Limits come from pipeline/config/channels.json (voice_budget): per release, per day and per month, counted from the spend
  ledger next to the cache. Over a limit nothing is sent; the result says "over_limit" and the release is blocked at 'voiced'.
* Only the channel's configured voice (OA: Adam, NEXORA: Matilda) produces a FINAL narration. Anything else is refused, so a
  draft or temporary voice can never reach an approval card (the QC gate checks the voice id again).
"""
import argparse, hashlib, json, os, shutil, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.path.join(HERE, "..", ".claude", "skills", "yt-voice")
sys.path.insert(0, VOICE_DIR); sys.path.insert(0, HERE)
import voice as V   # noqa: E402
import engine as E  # noqa: E402

CACHE = os.environ.get("PIPELINE_VOICE_CACHE", "/mnt/project-files/pipeline/voice_cache")


def cache_key(text, voice_id, model_id, settings, provider="elevenlabs"):
    return hashlib.sha256(E.canon({"provider": provider, "voice_id": voice_id, "model_id": model_id,
                                   "settings": settings or {}, "text": text}).encode()).hexdigest()


def spend_read(cache):
    p = os.path.join(cache, "spend.jsonl")
    if not os.path.exists(p):
        return []
    return [json.loads(x) for x in open(p) if x.strip()]


def spend_add(cache, rec):
    os.makedirs(cache, exist_ok=True)
    with open(os.path.join(cache, "spend.jsonl"), "a") as f:
        f.write(json.dumps({"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **rec}, ensure_ascii=False) + "\n")


def budget_check(cfg, channel, release, chars, cache, now=None):
    now = now or datetime.now(timezone.utc)
    b = cfg["channels"][channel]["voice_budget"]
    rows = [r for r in spend_read(cache) if r.get("event") == "paid"]
    day = now.strftime("%Y-%m-%d"); month = now.strftime("%Y-%m")
    used = {"release": sum(r["chars"] for r in rows if r.get("release") == release),
            "day": sum(r["chars"] for r in rows if r["at"].startswith(day)),
            "month": sum(r["chars"] for r in rows if r["at"].startswith(month))}
    lim = {"release": b["max_chars_per_release"], "day": b["max_chars_per_day"], "month": b["max_chars_per_month"]}
    over = [k for k in lim if used[k] + chars > lim[k]]
    return {"used": used, "limits": lim, "request_chars": chars, "over": over}


def run(a, cfg):
    ch = cfg["channels"][a.channel]["voice"]
    raw = open(a.script, encoding="utf-8").read()
    text, removed = V.spoken_text(raw)
    settings = json.loads(a.voice_settings) if a.voice_settings else None
    key = cache_key(text, ch["voice_id"], ch["model_id"], settings)
    hit = os.path.join(a.cache, key)
    os.makedirs(a.out_dir, exist_ok=True)
    out_wav, out_meta = os.path.join(a.out_dir, "narration.wav"), os.path.join(a.out_dir, "narration.voice.json")
    if os.path.isfile(os.path.join(hit, "narration.wav")) and os.path.isfile(os.path.join(hit, "narration.voice.json")):
        md = json.load(open(os.path.join(hit, "narration.voice.json")))
        if E.sha_file(os.path.join(hit, "narration.wav")) == md.get("audio_sha256"):
            shutil.copy(os.path.join(hit, "narration.wav"), out_wav); shutil.copy(os.path.join(hit, "narration.voice.json"), out_meta)
            spend_add(a.cache, {"event": "cache_hit", "key": key, "release": a.release, "chars": 0})
            return {"status": "cached", "cost_chars": 0, "key": key, "voice": out_wav, "meta": out_meta, "duration": md["duration"],
                    "voice_name": ch["name"], "final": True}
    opts = {"max_chars": cfg["channels"][a.channel]["voice_budget"]["max_chars_per_release"], "max_chunk_chars": 2500,
            "timeout_s": 180, "model": ch["model_id"], "language": "en", "auth": a.auth, "context": True}
    if settings:
        opts["voice_settings"] = settings
    tmp_dir = os.path.join(a.cache, key + ".partial")
    os.makedirs(tmp_dir, exist_ok=True)
    p = V.plan(text, "elevenlabs", ch["voice_id"], os.path.join(tmp_dir, "narration.wav"), opts)
    bud = budget_check(cfg, a.channel, a.release, p["characters"], a.cache)
    if bud["over"]:
        return {"status": "over_limit", "key": key, "budget": bud, "final": False}
    if not a.confirm:
        return {"status": "plan", "key": key, "characters": p["characters"], "chunks": len(p["chunks"]), "budget": bud,
                "voice_name": ch["name"], "removed_from_script": removed}
    spend_add(a.cache, {"event": "paid", "key": key, "release": a.release, "channel": a.channel, "chars": p["characters"],
                        "voice_id": ch["voice_id"], "model_id": ch["model_id"]})
    res = V.generate(p, opts, overwrite=True)
    if not os.path.exists(hit):
        os.replace(tmp_dir, hit)                         # the cache entry appears only once the audio and metadata are complete
    src = hit if os.path.isfile(os.path.join(hit, "narration.wav")) else tmp_dir
    spend_add(a.cache, {"event": "generated", "key": key, "release": a.release, "chars": 0, "duration": res["duration"]})
    shutil.copy(os.path.join(src, "narration.wav"), out_wav); shutil.copy(os.path.join(src, "narration.voice.json"), out_meta)
    return {"status": "generated", "cost_chars": p["characters"], "key": key, "voice": out_wav, "meta": out_meta,
            "duration": res["duration"], "words": res["words"], "voice_name": ch["name"], "final": True, "warnings": res["warnings"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", required=True); ap.add_argument("--release", required=True)
    ap.add_argument("--script", required=True); ap.add_argument("--out-dir", required=True)
    ap.add_argument("--voice-settings"); ap.add_argument("--auth", default=os.environ.get("YT_VOICE_AUTH", "proxy"))
    ap.add_argument("--cache", default=CACHE); ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = run(a, E.load_config())
    except V.VoiceError as ex:
        res = {"status": ex.status, "error": str(ex)[:300], "final": False}
    print(json.dumps(res, indent=1, ensure_ascii=False))
    return 0 if res.get("status") in ("cached", "generated", "plan") else 1


if __name__ == "__main__":
    sys.exit(main())
