"""Numerical QC of the host track over EVERY frame (no rendering needed):
presence of ATLAS in frame, foot sliding during contacts, joint jerks, mouth in pauses,
lip-sync correlation with the narration loudness. Prints a JSON report.

usage: python3 qc.py EPISODE.py [--out report.json]
"""
import json
import math
import subprocess
import sys
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render import load_episode, FPS, W, H        # noqa: E402
from host import Atlas                            # noqa: E402
from atlas_rig.pose import solve                  # noqa: E402
from atlas_rig.mathx import ap                    # noqa: E402

TRACK = ['neck', 'wrist_n', 'wrist_f', 'elbow_n', 'elbow_f', 'knee_n', 'knee_f', 'ankle_n', 'ankle_f', 'pelvis']


def rms_track(wav, offset, dur):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(offset), '-t', str(dur + 0.3), '-i', wav,
                          '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(float)
    hop = 16000 // FPS
    n = int(dur * FPS)
    return np.array([np.sqrt((a[i * hop:(i + 1) * hop] ** 2).mean() + 1e-9) if (i + 1) * hop <= len(a) else 0.0
                     for i in range(n)])


def run(ep_path):
    ep = load_episode(ep_path)
    atlas = Atlas()
    host = ep.build_host(atlas)
    n = int(round(ep.DUR * FPS))
    rig = atlas.rig
    prev = None
    prev_shot = None
    prev_contact = {}
    slides, jerks, off, head_off = [], [], [], []
    hist = []
    min_vis = 1.0
    mouth_pause = []
    words = host.words
    for i in range(n):
        t = i / FPS
        pose = host.pose(t, i)
        sol = solve(rig, pose)
        Ms = host.screen(t)
        js = {k: ap(Ms, sol.joints[k]) for k in TRACK if k in sol.joints}
        shot = host.shot_at(t)
        new_shot = shot is not prev_shot
        # presence: head (neck + helmet) and the visible share of tracked joints
        head = ap(Ms, sol.joints['neck'] + np.array([0.0, -60.0]))
        inside = [0 <= p[0] < W and 0 <= p[1] < H for p in js.values()]
        vis = sum(inside) / len(inside)
        if not (0 <= head[0] < W and 0 <= head[1] < H):
            head_off.append(i)
        # feet: contact points must not move while in contact (same shot)
        feet = host.perf.contacts(t)
        for s in 'nf':
            c = feet[s].get('contact')
            pts = feet[s].get('points') or []
            if c and pts:
                p = ap(Ms, np.asarray(pts[0], float))
                key = (s, c)
                if not new_shot and prev_contact.get(s, (None,))[0] == key:
                    slides.append(float(np.hypot(*(p - prev_contact[s][1]))))
                prev_contact[s] = (key, p)
            else:
                prev_contact[s] = (None, None)
        # jerk: second difference of joint positions inside a shot
        if new_shot:
            hist = []
        hist.append(js)
        if len(hist) >= 3:
            a, b, c = hist[-3], hist[-2], hist[-1]
            jerks.append(max(float(np.hypot(*(c[k] - 2 * b[k] + a[k]))) for k in c))
        # mouth must rest in pauses
        tw = t + 1 / FPS
        speaking = any(w['start'] - 0.06 <= tw <= w['end'] + 0.06 for w in words)
        if not speaking:
            mouth_pause.append(float(host.op[min(i, len(host.op) - 1)]))
        prev_shot = shot
    wav = ep.VOICE_WAV
    rms = rms_track(wav, getattr(ep, 'OFFSET', 0.0), ep.DUR)
    op = np.asarray(host.op[:len(rms)])
    corr = float(np.corrcoef(op[:len(rms)], rms[:len(op)])[0, 1]) if len(op) > 10 else float('nan')
    sl = np.array(slides) if slides else np.zeros(1)
    jk = np.array(jerks) if jerks else np.zeros(1)
    mp = np.array(mouth_pause) if mouth_pause else np.zeros(1)
    rep = dict(frames=n,
               head_offscreen_frames=len(head_off),
               foot_slide_px=dict(max=float(sl.max()), p99=float(np.percentile(sl, 99)), samples=len(slides)),
               joint_jerk_px=dict(max=float(jk.max()), p99=float(np.percentile(jk, 99))),
               mouth_in_pauses=dict(frames=len(mouth_pause), max_open=float(mp.max()),
                                    share_open_gt_0_15=float((mp > 0.15).mean())),
               lipsync_corr_open_vs_rms=corr)
    return rep


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('episode')
    p.add_argument('--out')
    a = p.parse_args()
    r = run(a.episode)
    s = json.dumps(r, indent=1)
    print(s)
    if a.out:
        open(a.out, 'w').write(s)
