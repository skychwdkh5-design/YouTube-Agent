"""EP002 creative preview builder (silent, 960x540, 12 fps, ESTIMATED timing; captions = locked VO text at 145 wpm inside each scene window).
Usage: python3 build_preview.py OUT_DIR --a1 CESIUM_A1_DIR [--only H1,H2] [--jobs 4]
Writes OUT_DIR/seg/<ID>.mp4 per scene and OUT_DIR/ep002_preview.mp4 (concat). Needs ffmpeg."""
import os, sys, glob, subprocess, argparse, json
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import W, H, FPS, Canvas, caption_track, draw_caption, badge
import scenes as S

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def vo_lines():
    return [l[4:].strip() for l in open(os.path.join(ROOT, 'script_draft_v1_2.md'), encoding='utf-8') if l.startswith('VO: ')]
def render_scene(args):
    sid, out, a1 = args
    sc = next(s for s in S.SCENES if s[0] == sid); _, start, dur, vos, fn = sc; vo = vo_lines(); X = {'a1_frames': sorted(glob.glob(os.path.join(a1, 'f*.png')))} if a1 else {}
    track = caption_track([vo[i - 1] for i in vos], dur); n = int(dur * FPS); path = os.path.join(out, 'seg', f'{sid}.mp4'); os.makedirs(os.path.dirname(path), exist_ok=True)
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'fast', path], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS; cv = fn(t, dur, X); draw_caption(cv, track, t); badge(cv)
        fr = cv.finish()
        if sid == 'E6' or sid == 'H4' and False: pass
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait(); return sid, n
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--a1'); ap.add_argument('--only'); ap.add_argument('--jobs', type=int, default=4); a = ap.parse_args()
    ids = [s[0] for s in S.SCENES if not a.only or s[0] in a.only.split(',')]
    with Pool(a.jobs) as pool:
        for sid, n in pool.imap_unordered(render_scene, [(i, a.out, a.a1) for i in ids]): print('done', sid, n, flush=True)
    if not a.only:
        lst = os.path.join(a.out, 'concat.txt'); open(lst, 'w').write(''.join(f"file 'seg/{s[0]}.mp4'\n" for s in S.SCENES))
        subprocess.check_call(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', os.path.join(a.out, 'ep002_preview.mp4')])
