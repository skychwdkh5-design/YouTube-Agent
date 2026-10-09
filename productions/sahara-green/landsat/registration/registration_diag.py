import json, sys, os, numpy as np
from PIL import Image
sys.path.insert(0, '/home/user/YouTube-Agent/.claude/skills/yt-geo')
import geostack as gs
Image.MAX_IMAGE_PIXELS = None
W = '/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/landsat_work/ep001'
OUT = '/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/diag'

def gray(a): return a.astype(np.float32).mean(axis=2) if a.ndim == 3 else a.astype(np.float32)
def grad(g):
    gy, gx = np.gradient(g); return np.hypot(gx, gy)
def hann(h, w): return np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
def pcorr(a, b):
    """shift (dx,dy) in px that moves b onto a (sub-pixel), peak ratio. positive dx: b content is right of a content."""
    h, w = a.shape
    wn = hann(h, w)
    A = np.fft.rfft2((a - a.mean()) * wn); B = np.fft.rfft2((b - b.mean()) * wn)
    R = A * np.conj(B); R /= np.abs(R) + 1e-9
    r = np.fft.irfft2(R, s=(h, w))
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    pk = r[iy, ix]
    def sub(m, p, n):
        l, c, rr = r[iy, (ix - 1) % w] if n == 'x' else r[(iy - 1) % h, ix], pk, r[iy, (ix + 1) % w] if n == 'x' else r[(iy + 1) % h, ix]
        d = (l - 2 * c + rr)
        return 0.0 if abs(d) < 1e-12 else 0.5 * (l - rr) / d
    sx, sy = sub(0, 0, 'x'), sub(0, 0, 'y')
    dx = ix + sx; dy = iy + sy
    if dx > w / 2: dx -= w
    if dy > h / 2: dy -= h
    r2 = r.copy(); r2[max(0, iy - 3):iy + 4, :] = r2[max(0, iy - 3):iy + 4, :] * 0  # crude sidelobe mask
    side = np.sort(np.abs(r.ravel()))[-50:].mean()
    return float(-dx), float(-dy), float(pk), float(np.std(r))

res = {'stacks': {}}
for name, tag in (('eo', 'East Oweinat'), ('toshkaW', 'Toshka W (path 176)'), ('toshkaE', 'Toshka E (path 175)')):
    g = json.load(open(f'{W}/prev_{name}/grid.json'))
    st = {'grid': {k: g[k] for k in ('epsg', 'x0', 'y_top', 'pixel_m', 'width', 'height', 'aoi')}, 'scenes': []}
    frames = {}
    for s in g['scenes']:
        im, info = gs.read_geotiff(f'{W}/{s["src"]}')
        arr = np.asarray(Image.open(f'{W}/prev_{name}/{s["png"]}').convert('RGB'))
        frames[s['id']] = arr
        raw = np.asarray(im)
        rawg = raw.max(axis=2) if raw.ndim == 3 else raw
        valid = rawg > 0
        ys, xs = np.where(valid)
        # AOI window in scene pixel coords
        x_l = (g['x0'] - info['x0']) / info['dx']; x_r = x_l + g['width']
        y_t = (info['y0'] - g['y_top']) / info['dy']; y_b = y_t + g['height']
        xl, xr, yt, yb = int(max(0, x_l)), int(min(info['width'], x_r)), int(max(0, y_t)), int(min(info['height'], y_b))
        win = valid[yt:yb, xl:xr]
        sub = ((g['x0'] - info['x0']) / info['dx']) % 1, ((info['y0'] - g['y_top']) / info['dy']) % 1
        nd = float((arr.max(axis=2) == 0).mean())
        stable = arr.max(axis=2) > 0
        st['scenes'].append({
            'id': s['id'], 'label': s['label'], 'epsg': info['epsg'], 'pixel_m': [info['dx'], info['dy']],
            'pixel_is_area': info['pixel_is_area'], 'origin': [info['x0'], info['y0']], 'size': [info['width'], info['height']],
            'subpixel_phase_vs_stack_grid': [round(sub[0], 3), round(sub[1], 3)],
            'valid_fraction_scene': round(float(valid.mean()), 3),
            'valid_bbox_px': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            'valid_fraction_in_AOI_window': round(float(win.mean()), 4) if win.size else None,
            'stack_frame_nodata_fraction': round(nd, 4),
            'mean_rgb_valid': [round(float(arr[..., c][stable].mean()), 1) for c in range(3)],
            'std_gray_valid': round(float(gray(arr)[stable].std()), 1)})
    # registration vs reference (latest frame) and adjacent pairs, whole frame + 3x3 tiles
    ids = list(frames); ref = ids[-1]
    G = {k: grad(gray(v)) for k, v in frames.items()}
    def tiles(a, b, n=3):
        h, w = a.shape; out = []
        for i in range(n):
            for j in range(n):
                sl = (slice(i * h // n, (i + 1) * h // n), slice(j * w // n, (j + 1) * w // n))
                aa, bb = a[sl], b[sl]
                if aa.size == 0 or (aa > 0).mean() < .5: out.append(None); continue
                dx, dy, pk, sd = pcorr(aa, bb); out.append([round(dx, 2), round(dy, 2), round(pk / (sd + 1e-9), 1)])
        return out
    st['registration'] = []
    pairs = [(k, ref) for k in ids[:-1]] + [(ids[i], ids[i + 1]) for i in range(len(ids) - 2)]
    for a_id, b_id in pairs:
        dx, dy, pk, sd = pcorr(G[b_id], G[a_id])  # shift of a relative to b
        st['registration'].append({'moving': a_id, 'reference': b_id, 'shift_px_x': round(dx, 2), 'shift_px_y': round(dy, 2),
                                   'peak_over_noise': round(pk / (sd + 1e-9), 1), 'tiles_3x3_dx_dy_snr': tiles(G[b_id], G[a_id])})
    res['stacks'][name] = st
    np.savez_compressed(f'{OUT}/{name}_frames.npz', **frames)
json.dump(res, open(f'{OUT}/registration_diag.json', 'w'), indent=1)
print('ok')
