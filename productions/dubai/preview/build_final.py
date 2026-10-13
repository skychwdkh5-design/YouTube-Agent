"""EP002 final builder: scenes rendered on the REAL narration timeline (sync.py), captions from provider word timings, native resolution (EP002_SCALE=2 -> 1920x1080) and fps.
    python3 build_final.py OUT_DIR [--scale 2] [--fps 30] [--a1 DIR] [--only H0,H1] [--jobs 4] [--crf 19] [--mux]
Writes OUT_DIR/seg/<ID>.mp4 (video only, resumable: existing segments are kept unless --force); --mux concatenates them, builds the audio (narration slices, silence elsewhere),
normalises it to -16 LUFS (two-pass loudnorm) and writes OUT_DIR/ep002_final.mp4 + captions (SRT/VTT). Never calls an API."""
import os, sys, glob, json, subprocess, argparse
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--scale', type=float, default=2.0); ap.add_argument('--fps', type=int, default=30); ap.add_argument('--a1'); ap.add_argument('--only')
ap.add_argument('--jobs', type=int, default=4); ap.add_argument('--crf', type=int, default=19); ap.add_argument('--mux', action='store_true'); ap.add_argument('--force', action='store_true'); ap.add_argument('--nocaps', action='store_true')
A = ap.parse_args(); os.environ['EP002_SCALE'] = str(A.scale); os.environ['EP002_FPS'] = str(A.fps)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import W, H, FPS, PW, PH, Canvas, draw_caption
from PIL import Image
import scenes as S, sync
SC = [(s[0], s[1], s[2], s[3]) for s in S.SCENES]; PLAN, OFFSET = sync.plan(SC)
def render_scene(args):
    sid, = args; sc = next(s for s in S.SCENES if s[0] == sid); _, _, d_est, vos, fn = sc; win = PLAN[sid]; path = os.path.join(A.out, 'seg', f'{sid}.mp4'); os.makedirs(os.path.dirname(path), exist_ok=True)
    X = {'a1_frames': sorted(glob.glob(os.path.join(A.a1, 'f*.png')))} if A.a1 else {}; track = [] if A.nocaps else [tuple(c) for c in sync.cues(win['words'])]; n = int(round(win['dur'] * FPS)); tmp = path + '.part.mp4'
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{PW}x{PH}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(A.crf), '-preset', 'medium', '-g', str(FPS * 2), tmp], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS; te = win['warp'](t); fr = fn(te, d_est, X).finish(); amt = S.PUSH.get(sid, 0.0)
        if amt:                                                   # slow push on text/graphic scenes; captions are drawn after, so they stay put
            s = 1 + amt * kit.smr(te / d_est); fr = fr.transform((PW, PH), Image.AFFINE, (1 / s, 0, PW / 2 - PW / 2 / s, 0, 1 / s, PH / 2 - PH / 2 / s), resample=Image.BICUBIC)
        cv = Canvas(fr); draw_caption(cv, track, t); p.stdin.write(cv.finish().tobytes())
    p.stdin.close(); p.wait(); os.replace(tmp, path); return sid, n
def main():
    from multiprocessing import Pool
    ids = [s[0] for s in S.SCENES if not A.only or s[0] in A.only.split(',')]
    todo = [i for i in ids if A.force or not os.path.exists(os.path.join(A.out, 'seg', f'{i}.mp4'))]
    with Pool(A.jobs) as pool:
        for sid, n in pool.imap_unordered(render_scene, [(i,) for i in todo]): print('done', sid, n, flush=True)
    if A.mux: mux()
def loudnorm(src, dst, target=-16.0, tp=-1.5, lra=11):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', src, '-af', f'loudnorm=I={target}:TP={tp}:LRA={lra}:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = f"loudnorm=I={target}:TP={tp}:LRA={lra}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', af, '-ar', '48000', '-ac', '2', dst], check=True); return j
def mux():
    lst = os.path.join(A.out, 'concat.txt'); open(lst, 'w').write(''.join(f"file 'seg/{s[0]}.mp4'\n" for s in S.SCENES))
    vid = os.path.join(A.out, 'video_only.mp4'); subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid], check=True)
    raw = os.path.join(A.out, 'audio_raw.wav'); dur = sync.assemble_audio(PLAN, raw); norm = os.path.join(A.out, 'audio_norm.wav'); j = loudnorm(raw, norm); json.dump(j, open(os.path.join(A.out, 'loudnorm_measure.json'), 'w'), indent=1)
    final = os.path.join(A.out, 'ep002_final.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', vid, '-i', norm, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', final], check=True)
    cues = []
    for s in S.SCENES:
        w = PLAN[s[0]]
        for a, b, t in sync.cues(w['words']): cues.append((w['start'] + a, w['start'] + b, t))
    def ts(x, sep): h = int(x // 3600); m = int(x % 3600 // 60); sx = x % 60; return f'{h:02d}:{m:02d}:{int(sx):02d}{sep}{int(round((sx - int(sx)) * 1000)):03d}'
    with open(os.path.join(A.out, 'ep002.srt'), 'w') as f:
        for i, (a, b, t) in enumerate(cues, 1): f.write(f'{i}\n{ts(a, ",")} --> {ts(b, ",")}\n{t}\n\n')
    with open(os.path.join(A.out, 'ep002.vtt'), 'w') as f:
        f.write('WEBVTT\n\n')
        for a, b, t in cues: f.write(f'{ts(a, ".")} --> {ts(b, ".")}\n{t}\n\n')
    print('muxed', final, round(dur, 2))
if __name__ == '__main__': main()
