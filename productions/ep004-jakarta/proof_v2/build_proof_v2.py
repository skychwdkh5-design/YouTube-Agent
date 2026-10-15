"""EP004 S3 V2 proof: "Cutaway Descent" (orbitalatlas.subsidence3d) -> match dissolve from the top view -> EVIDENCE MAP PENDING.
13.5 s, 1920x1080, 30 fps. Free: no TTS, synthesised CC0 sound (orbitalatlas.sfx), no third-party media.
    python3 productions/ep004-jakarta/proof_v2/build_proof_v2.py stills OUTDIR [t ...]
    python3 productions/ep004-jakarta/proof_v2/build_proof_v2.py render OUT.mp4 [--workers 4]
"""
import os, sys, json, wave, subprocess
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from orbitalatlas import illustrate as I, subsidence3d as S3D, sequence as S, transitions as TR, sfx

SIZE = (1920, 1080); FPS = 30
# cues follow the picture events (sfx.mix places them; >= 0.25 s apart)
CUES = [dict(t=0.20, kind="whoosh", why="satellite arrives"), dict(t=1.65, kind="sweep", why="pulse 1"), dict(t=2.30, kind="tick", why="echo 1 returns"),
        dict(t=3.20, kind="whoosh", why="camera dives to the cut face"), dict(t=4.20, kind="rise", why="pumping starts"), dict(t=4.50, kind="ui_blip", why="label"),
        dict(t=5.95, kind="ui_blip", why="label"), dict(t=7.20, kind="whoosh", why="camera rises for pass 2"), dict(t=7.50, kind="sweep", why="pulse 2"),
        dict(t=8.10, kind="tick", why="echo 2 returns"), dict(t=8.75, kind="ui_blip", why="extra path"), dict(t=9.95, kind="impact", why="LINE OF SIGHT lockup"),
        dict(t=12.0, kind="whoosh", why="camera to the top view")]


def program(size=SIZE):
    a = S3D.CutawayRadarDiagram(size, 12.8); b = I.EvidencePending(size, 1.3)
    return S.Sequence([S.Shot(a, 12.8, "cutaway_radar"), S.Shot(b, 1.3, "evidence_pending")], [TR.Dissolve(0.6)])


def audio(path, dur):
    silent = path + ".silent.wav"
    with wave.open(silent, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(sfx.SR); w.writeframes(np.zeros((int(dur * sfx.SR), 2), np.int16).tobytes())
    raw = path + ".raw.wav"; rep = sfx.mix(silent, CUES, dur, raw, normalise=False); os.remove(silent)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "volume=8dB,alimiter=limit=0.70", path], check=True); os.remove(raw); rep["proof_gain_db"] = 8; return rep


if __name__ == "__main__":
    cmd = sys.argv[1]; seq = program()
    if cmd == "stills":
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        for t in [float(x) for x in sys.argv[3:]] or [0.5, 2.0, 3.5, 5.0, 6.5, 8.0, 9.0, 10.5, 11.5, 12.5, 13.2]: seq.render(t).save(os.path.join(out, f"t{t:06.2f}.png"))
        print("duration", seq.duration, "problems", seq.problems)
    elif cmd == "render":
        out = sys.argv[2]; workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
        wav = out + ".wav"; rep = audio(wav, seq.duration); json.dump(rep, open(out + ".sfx.json", "w"), indent=1)
        print("frames", S.render_video(seq, out, FPS, workers, audio=wav))
