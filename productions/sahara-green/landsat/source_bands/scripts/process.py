"""EP001 source-band preliminary stacks. TOA reflectance, one fixed stretch per stack, common grid per path.
Usage: python3 -I process.py STACK   (EO | TW | TE)"""
import sys, os, json, re, numpy as np
from PIL import Image
sys.path.insert(0, '/home/user/YouTube-Agent/.claude/skills/yt-geo')
import geostack as gs
Image.MAX_IMAGE_PIXELS = None
S = '/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad'
W = S + '/landsat_work/ep001'
SB = W + '/src_bands'
OUT = S + '/acq/out'; os.makedirs(OUT, exist_ok=True)
SCN = {
 'EO': [('1984','LT05_L1TP_177044_19840826_20200918_02_T1'),('2000','LT05_L1TP_177044_20000111_20200907_02_T1'),('2010','LT05_L1TP_177044_20100122_20200825_02_T1'),('2016','LC08_L1TP_177044_20160107_20200907_02_T1'),('2024','LC09_L1TP_177044_20240105_20240105_02_T1')],
 'TW': [('1999','LT05_L1TP_176044_19990101_20200908_02_T1'),('2002','LT05_L1TP_176044_20020109_20200905_02_T1'),('2011','LT05_L1TP_176044_20110102_20200823_02_T1'),('2021','LC08_L1TP_176044_20211113_20211125_02_T1')],
 'TE': [('1999','LT05_L1TP_175044_19990110_20200908_02_T1'),('2002','LT05_L1TP_175044_20020118_20200905_02_T1'),('2011','LT05_L1TP_175044_20110111_20200823_02_T1'),('2021','LC08_L1TP_175044_20211106_20211117_02_T1')]}
GRID_SRC = {'EO': 'prev_eo', 'TW': 'prev_toshkaW', 'TE': 'prev_toshkaE'}
def path_of(sid, suf):
    for d in (f'{SB}/{sid}', W + '/l1', W + '/l1_2024'):
        p = f'{d}/{sid}_{suf}'
        if os.path.exists(p): return p
    raise FileNotFoundError(f'{sid}_{suf}')
def mtl(sid):
    t = open(path_of(sid, 'MTL.txt')).read()
    g = lambda k: float(re.search(rf'\b{k} = ([-0-9.Ee+]+)', t).group(1))
    return g, re.search(r'DATE_ACQUIRED = (\S+)', t).group(1), g('SUN_ELEVATION')
def band_tag(sid): return [3, 2, 1] if sid.startswith('LT05') else [4, 3, 2]   # R,G,B
def read_band(sid, b):
    im, info = gs.read_geotiff(path_of(sid, f'B{b}.TIF'))
    a = np.asarray(im)
    if info['pixel_is_area'] is False:   # PixelIsPoint: tie point is the pixel centre
        info = dict(info, x0=info['x0'] - info['dx'] / 2, y0=info['y0'] + info['dy'] / 2)
    return a, info
def window(a, info, grid, order=1):
    """resample band a (30 m, north-up) onto grid; exact crop when lattice offset is an integer, else bilinear"""
    fx = (grid['x0'] - info['x0']) / info['dx']; fy = (info['y0'] - grid['y_top']) / info['dy']
    ix, iy = int(np.floor(fx)), int(np.floor(fy)); rx, ry = fx - ix, fy - iy
    h, w = grid['height'], grid['width']
    pad = ((max(0, -iy), max(0, iy + h + 1 - a.shape[0])), (max(0, -ix), max(0, ix + w + 1 - a.shape[1])))
    ap = np.pad(a.astype(np.float32), pad)
    y0, x0 = iy + pad[0][0], ix + pad[1][0]
    blk = ap[y0:y0 + h + 1, x0:x0 + w + 1]
    if abs(rx) < 1e-6 and abs(ry) < 1e-6: return blk[:h, :w], (rx, ry)
    out = (blk[:h, :w] * (1 - rx) * (1 - ry) + blk[:h, 1:w + 1] * rx * (1 - ry) + blk[1:h + 1, :w] * (1 - rx) * ry + blk[1:h + 1, 1:w + 1] * rx * ry)
    return out, (rx, ry)
def grad(g): gy, gx = np.gradient(g); return np.hypot(gx, gy)
def pcorr(a, b):
    h, w = a.shape; wn = np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
    A = np.fft.rfft2((a - a.mean()) * wn); B = np.fft.rfft2((b - b.mean()) * wn)
    R = A * np.conj(B); R /= np.abs(R) + 1e-9; r = np.fft.irfft2(R, s=(h, w))
    iy, ix = np.unravel_index(np.argmax(r), r.shape); pk = r[iy, ix]
    def sub(l, c, rr): d = l - 2 * c + rr; return 0.0 if abs(d) < 1e-12 else 0.5 * (l - rr) / d
    sx = sub(r[iy, (ix - 1) % w], pk, r[iy, (ix + 1) % w]); sy = sub(r[(iy - 1) % h, ix], pk, r[(iy + 1) % h, ix])
    dx, dy = ix + sx, iy + sy
    if dx > w / 2: dx -= w
    if dy > h / 2: dy -= h
    return float(-dx), float(-dy), float(pk / (np.std(r) + 1e-9))
def main(stack):
    g0 = json.load(open(f'{W}/{GRID_SRC[stack]}/grid.json'))
    grid = {k: g0[k] for k in ('epsg', 'x0', 'y_top', 'pixel_m', 'width', 'height')}
    grid['x0'] -= 15.0; grid['y_top'] += 15.0   # snap to the Landsat 30 m lattice (browse-derived grid was half a pixel off): no resampling needed
    rep = {'stack': stack, 'grid': grid, 'scenes': []}
    refl = {}; valid = {}; qa = {}
    for label, sid in SCN[stack]:
        g, date, sun = mtl(sid); rgb = []; fr = None
        for b in band_tag(sid):
            a, info = read_band(sid, b)
            if info['epsg'] != grid['epsg']: raise SystemExit(f'{sid}: EPSG {info["epsg"]} != {grid["epsg"]}')
            win, frac = window(a, info, grid)
            fr = frac
            dn = win
            r = (g(f'REFLECTANCE_MULT_BAND_{b}') * dn + g(f'REFLECTANCE_ADD_BAND_{b}')) / np.sin(np.radians(sun))
            r[dn <= 0] = np.nan; rgb.append(r.astype(np.float32))
            del a
        qim, qi = gs.read_geotiff(path_of(sid, 'QA_PIXEL.TIF')); qarr = np.asarray(qim)
        if qi['pixel_is_area'] is False: qi = dict(qi, x0=qi['x0'] - qi['dx'] / 2, y0=qi['y0'] + qi['dy'] / 2)
        qwin = np.round(window(qarr.astype(np.float32), qi, grid)[0]).astype(np.uint32) if True else None
        cube = np.stack(rgb, 2); v = np.isfinite(cube).all(2) & ((qwin & 1) == 0)
        cloud = (((qwin >> 3) & 1) | ((qwin >> 4) & 1) | ((qwin >> 1) & 1)).astype(bool) & v
        refl[label] = cube; valid[label] = v
        rep['scenes'].append({'label': label, 'displayId': sid, 'date': date, 'sun_elevation_deg': round(sun, 2), 'bands_RGB': band_tag(sid),
            'lattice_offset_px_x_y': [round(fr[0], 3), round(fr[1], 3)], 'valid_fraction_AOI': round(float(v.mean()), 4),
            'qa_cloud_shadow_fraction_AOI': round(float(cloud.mean()), 5),
            'median_reflectance_rgb_valid': [round(float(np.nanmedian(cube[..., c][v])), 4) for c in range(3)]})
        print(stack, label, 'ok', flush=True)
    # one fixed stretch per stack: pooled percentiles over all valid pixels of all frames
    pool = np.concatenate([refl[k][valid[k]][::40] for k in refl]); lo = np.percentile(pool, 1, axis=0); hi = np.percentile(pool, 99.5, axis=0)
    rep['stretch'] = {'method': 'TOA reflectance; per-channel pooled p1..p99.5 over all frames of the stack, linear, gamma 1/1.6', 'lo': [round(float(x), 4) for x in lo], 'hi': [round(float(x), 4) for x in hi]}
    frames = {}
    for k, cube in refl.items():
        x = np.clip((cube - lo) / (hi - lo), 0, 1) ** (1 / 1.6); x[~valid[k]] = 0
        frames[k] = (x * 255 + 0.5).astype(np.uint8)
    # registration on red-band gradient, reference = latest
    labels = list(refl); ref = labels[-1]; G = {}
    for k in labels:
        r = np.nan_to_num(refl[k][..., 0], nan=0.0); G[k] = grad(r) * valid[k]
    def tiles(a, b, n=3):
        h, w = a.shape; o = []
        for i in range(n):
            for j in range(n):
                sl = (slice(i * h // n, (i + 1) * h // n), slice(j * w // n, (j + 1) * w // n))
                o.append([round(v, 2) for v in pcorr(a[sl], b[sl])] if (a[sl] > 0).mean() > .5 and (b[sl] > 0).mean() > .5 else None)
        return o
    reg = []
    for a, b in [(k, ref) for k in labels[:-1]] + [(labels[i], labels[i + 1]) for i in range(len(labels) - 2)]:
        dx, dy, snr = pcorr(G[b], G[a]); reg.append({'moving': a, 'reference': b, 'dx_px': round(dx, 2), 'dy_px': round(dy, 2), 'snr': round(snr, 1), 'tiles_3x3_dx_dy_snr': tiles(G[b], G[a])})
    rep['registration'] = reg
    # seasonal/radiometric: median reflectance on pixels valid in all frames and low-NIR-independent proxy (red band percentiles)
    allv = np.logical_and.reduce([valid[k] for k in labels])
    rep['common_valid_fraction'] = round(float(allv.mean()), 4)
    rep['median_red_common_valid'] = {k: round(float(np.nanmedian(refl[k][..., 0][allv])), 4) for k in labels}
    np.savez_compressed(f'{OUT}/{stack}_refl_f16.npz', **{k: v.astype(np.float16) for k, v in refl.items()}, **{'valid_' + k: v for k, v in valid.items()})
    for k, f in frames.items(): Image.fromarray(f).save(f'{OUT}/{stack}_{k}.png')
    json.dump(rep, open(f'{OUT}/{stack}_report.json', 'w'), indent=1)
    print('DONE', stack, flush=True)
if __name__ == '__main__': main(sys.argv[1])
