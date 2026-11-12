"""Episode renderer: background scene (PIL, 1920x1080) + ATLAS host + top overlays,
rendered in parallel chunks, then concatenated and muxed with the mixed audio.

An episode module provides:
    DUR, VOICE_WAV, VOICE_JSON
    build_host(atlas) -> Host            (shots + actions)
    background(t) -> PIL.Image RGB        (scene graphics under ATLAS)
    overlay(t, img) -> None               (optional, drawn above ATLAS: labels/credits)
    audio_filter(work) -> (inputs, filtergraph)   (optional SFX mix)
"""
import importlib
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FPS, W, H = 30, 1920, 1080


def load_episode(mod_path):
    d, f = os.path.split(os.path.abspath(mod_path))
    sys.path.insert(0, d)
    return importlib.import_module(os.path.splitext(f)[0])


_CTX = {}


def _ctx(mod_path):
    if 'ep' not in _CTX:
        from host import Atlas
        ep = load_episode(mod_path)
        atlas = Atlas()
        host = ep.build_host(atlas)
        _CTX.update(ep=ep, atlas=atlas, host=host)
    return _CTX['ep'], _CTX['atlas'], _CTX['host']


def frame(mod_path, i, debug=False):
    ep, atlas, host = _ctx(mod_path)
    t = i / FPS
    bg = ep.background(t).convert('RGB')
    can = np.dstack([np.asarray(bg, np.float32) / 255, np.ones((H, W, 1), np.float32)])
    pose = host.pose(t, i)
    sol = atlas.solve(pose)
    atlas.draw(can, sol, host.screen(t), host.face(t, i))
    img = Image.fromarray((np.clip(can[..., :3], 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')
    if hasattr(ep, 'overlay'):
        ep.overlay(t, img)
    if debug:
        from atlas_rig.character import draw_debug
        draw_debug(img, sol, host.screen(t), pose, host.perf.contacts(t), atlas.rig, t, 'debug')
    return img


def _chunk(args):
    mod_path, a, b, out, debug = args
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16',
                           '-pix_fmt', 'yuv420p', '-g', '60', out], stdin=subprocess.PIPE)
    for i in range(a, b):
        ff.stdin.write(frame(mod_path, i, debug).tobytes())
    ff.stdin.close()
    ff.wait()
    return out


def render_video(mod_path, work, out_video, f0=0, f1=None, jobs=4, chunk=150, debug=False):
    ep = load_episode(mod_path)
    f1 = f1 if f1 is not None else int(round(ep.DUR * FPS))
    os.makedirs(work, exist_ok=True)
    tasks = []
    for k, a in enumerate(range(f0, f1, chunk)):
        tasks.append((mod_path, a, min(f1, a + chunk), os.path.join(work, f'chunk_{a:06d}.mp4'), debug))
    t0 = time.time()
    with ProcessPoolExecutor(jobs) as ex:
        outs = list(ex.map(_chunk, tasks))
    lst = os.path.join(work, 'chunks.txt')
    open(lst, 'w').write(''.join(f"file '{o}'\n" for o in outs))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out_video], check=True)
    print(f'video {f1 - f0} frames in {time.time() - t0:.0f}s -> {out_video}')
    return out_video


def mux(video, audio, out, t0=0.0, dur=None):
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', video, '-ss', str(t0)]
    if dur:
        cmd += ['-t', str(dur)]
    cmd += ['-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-shortest', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    return out


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('episode')
    p.add_argument('cmd', choices=['frames', 'video'])
    p.add_argument('out')
    p.add_argument('--t', nargs='*', type=float, default=[])
    p.add_argument('--f0', type=int, default=0)
    p.add_argument('--f1', type=int, default=None)
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--debug', action='store_true')
    a = p.parse_args()
    if a.cmd == 'frames':
        os.makedirs(a.out, exist_ok=True)
        for t in a.t:
            frame(a.episode, int(round(t * FPS)), a.debug).save(os.path.join(a.out, f't{t:07.2f}.png'))
    else:
        render_video(a.episode, a.out + '_work', a.out, a.f0, a.f1, a.jobs, debug=a.debug)
