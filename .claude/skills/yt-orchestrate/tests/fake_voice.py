#!/usr/bin/env python3
"""TEST STUB for yt-voice (no network, no cost): silent wav + evenly spaced word timings in the yt-voice/1 format."""
import os, argparse, hashlib, json, subprocess, sys
ap = argparse.ArgumentParser()
ap.add_argument("--script"); ap.add_argument("--output"); ap.add_argument("--auth"); ap.add_argument("--confirm", action="store_true"); ap.add_argument("--max-chars")
a = ap.parse_args()
if os.environ.get("FAKE_VOICE_LOG"):
    open(os.environ["FAKE_VOICE_LOG"], "a").write("CALL\n")      # counts paid calls
if os.environ.get("FAKE_VOICE_FAIL"):
    print(json.dumps({"status": "network_error", "error": "simulated"})); sys.exit(1)
text = open(a.script, encoding="utf-8").read()
words = text.split()
dur = len(words) / 2.5
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", ("anullsrc=r=24000:cl=mono" if os.environ.get("FAKE_VOICE_SILENT") else "sine=frequency=220:sample_rate=24000,volume=0.3"), "-t", f"{dur:.3f}", a.output], check=True)
meta = {"schema": "yt-voice/1", "provider": "TEST-STUB", "model_id": "stub", "voice_id": "stub", "voice_name": "stub", "voice_source": "test", "language": "en", "audio": a.output.split("/")[-1],
        "audio_sha256": hashlib.sha256(open(a.output, "rb").read()).hexdigest(), "duration": dur, "characters": len(text), "text": text,
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "chunks": [], "timing": {"source": "provider", "level": "word"}, "fake": True,
        "words": [{"text": w, "start": round(i / 2.5, 3), "end": round(i / 2.5 + 0.38, 3)} for i, w in enumerate(words)]}
json.dump(meta, open(a.output.rsplit(".", 1)[0] + ".voice.json", "w"))
print(json.dumps({"status": "ok", "characters": len(text)}))
