"""EP004 S3 proof: radar geometry illustration -> flash dip -> EVIDENCE MAP PENDING. 13.5 s, 1920x1080, 30 fps. Free: no TTS, synthesised CC0 sound.
    python3 productions/ep004-jakarta/proof/build_proof.py stills OUTDIR [t ...]      # PNG stills
    python3 productions/ep004-jakarta/proof/build_proof.py render OUT.mp4 [--workers 4] # silent picture + CC0 effects
"""
import os, sys, json, wave, subprocess
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from orbitalatlas import illustrate as I, sequence as S, transitions as TR, sfx

SIZE = (1920, 1080); FPS = 30
CUES = [dict(t=0.25, kind="whoosh"), dict(t=1.30, kind="sweep"), dict(t=2.70, kind="ui_blip"), dict(t=4.20, kind="rise"), dict(t=6.20, kind="sweep"),
        dict(t=7.90, kind="ui_blip"), dict(t=8.55, kind="whoosh"), dict(t=9.45, kind="ui_blip"), dict(t=10.25, kind="ui_blip"), dict(t=11.62, kind="impact")]


def program(size=SIZE):
    a = I.RadarGeometryDiagram(size, 12.0); b = I.EvidencePending(size, 2.0)
    return S.Sequence([S.Shot(a, 12.0, "radar_geometry"), S.Shot(b, 2.0, "evidence_pending")], [TR.FlashDip(0.5, peak=0.7)])


def audio(path, dur):
    silent = path + ".silent.wav"
    with wave.open(silent, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(sfx.SR); w.writeframes(np.zeros((int(dur * sfx.SR), 2), np.int16).tobytes())
    raw = path + ".raw.wav"; rep = sfx.mix(silent, CUES, dur, raw, normalise=False); os.remove(silent)
    # effects-only proof: raise the level so it is audible on an iPad (the real mix ducks effects >= 12 dB under the narrator); true peak stays under -3 dBFS
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "volume=8dB,alimiter=limit=0.70", path], check=True); os.remove(raw); rep["proof_gain_db"] = 8; return rep


if __name__ == "__main__":
    cmd = sys.argv[1]; seq = program()
    if cmd == "stills":
        out = sys.argv[2]; os.makedirs(out, exist_ok=True); ts = [float(x) for x in sys.argv[3:]] or [0.5, 1.7, 3.5, 5.2, 6.8, 8.3, 8.9, 9.8, 10.6, 11.2, 11.75, 12.6]
        for t in ts: seq.render(t).save(os.path.join(out, f"t{t:06.2f}.png"))
        print("duration", seq.duration, "problems", seq.problems)
    elif cmd == "render":
        out = sys.argv[2]; workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
        wav = out + ".wav"; rep = audio(wav, seq.duration); json.dump(rep, open(out + ".sfx.json", "w"), indent=1)
        n = S.render_video(seq, out, FPS, workers, audio=wav); print("frames", n)
