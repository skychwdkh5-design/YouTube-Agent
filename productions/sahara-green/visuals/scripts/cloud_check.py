import sys, json, os, numpy as np
from collections import deque
from PIL import Image, ImageDraw
sys.path.insert(0, '/home/user/YouTube-Agent/.claude/skills/yt-geo'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geostack as gs, vis_common as c
Image.MAX_IMAGE_PIXELS = None
SB = '/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/landsat_work/ep001/src_bands/'
SC = {'TW': {'1999': 'LT05_L1TP_176044_19990101_20200908_02_T1', '2002': 'LT05_L1TP_176044_20020109_20200905_02_T1', '2011': 'LT05_L1TP_176044_20110102_20200823_02_T1', '2021': 'LC08_L1TP_176044_20211113_20211125_02_T1'},
      'TE': {'1999': 'LT05_L1TP_175044_19990110_20200908_02_T1', '2002': 'LT05_L1TP_175044_20020118_20200905_02_T1', '2011': 'LT05_L1TP_175044_20110111_20200823_02_T1', '2021': 'LC08_L1TP_175044_20211106_20211117_02_T1'}}
Y0, X0, CH, CW = 60, 312, 2160, 3840
gW = json.load(open(c.ACQ + 'TW_report.json'))['grid']; gE = json.load(open(c.ACQ + 'TE_report.json'))['grid']
cx = int(round((gE['x0'] - gW['x0']) / 30)); ry = int(round((gW['y_top'] - gE['y_top']) / 30))
def qa_on_grid(sid, g):
    im, info = gs.read_geotiff(SB + f'{sid}/{sid}_QA_PIXEL.TIF'); a = np.asarray(im).astype(np.uint32)
    if info['pixel_is_area'] is False: info = dict(info, x0=info['x0'] - 15, y0=info['y0'] + 15)
    fx = int(round((g['x0'] - info['x0']) / 30)); fy = int(round((info['y0'] - g['y_top']) / 30))
    return a[fy:fy + g['height'], fx:fx + g['width']]
def blobs(mask, blk=16):
    h, w = mask.shape; hb, wb = h // blk, w // blk
    r = mask[:hb * blk, :wb * blk].reshape(hb, blk, wb, blk).any((1, 3)); seen = np.zeros_like(r); out = []
    for y in range(hb):
        for x in range(wb):
            if r[y, x] and not seen[y, x]:
                q = deque([(y, x)]); seen[y, x] = 1; pts = []
                while q:
                    j, i = q.popleft(); pts.append((j, i))
                    for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                        jj, ii = j + dj, i + di
                        if 0 <= jj < hb and 0 <= ii < wb and r[jj, ii] and not seen[jj, ii]: seen[jj, ii] = 1; q.append((jj, ii))
                ys = [p[0] for p in pts]; xs = [p[1] for p in pts]
                out.append({'blocks': len(pts), 'bbox_x0y0x1y1_in_crop_px': [min(xs) * blk, min(ys) * blk, (max(xs) + 1) * blk, (max(ys) + 1) * blk]})
    return sorted(out, key=lambda b: -b['blocks'])[:6]
res = {'display_crop_union_px': {'y0': Y0, 'x0': X0, 'h': CH, 'w': CW}, 'flags': 'QA_PIXEL bit1 dilated cloud, bit2 cirrus, bit3 cloud, bit4 cloud shadow; high confidence = bits8-9 (cloud) or 10-11 (shadow) == 3', 'scenes': {}}
for y in ('1999', '2002', '2011', '2021'):
    full = np.zeros((CH, CW), np.uint8); hc = np.zeros((CH, CW), np.uint8)
    for p, g, (ox, oy) in (('TW', gW, (0, 0)), ('TE', gE, (cx, ry))):
        q = qa_on_grid(SC[p][y], g)
        flag = (((q >> 1) & 1) | ((q >> 2) & 1) | ((q >> 3) & 1) | ((q >> 4) & 1)).astype(bool)
        high = (((q >> 8) & 3) == 3) | (((q >> 10) & 3) == 3)
        # place into union then crop
        U = np.zeros((max(gW['height'], ry + gE['height']), cx + gE['width']), np.uint8); H2 = U.copy()
        U[oy:oy + g['height'], ox:ox + g['width']] = flag; H2[oy:oy + g['height'], ox:ox + g['width']] = high
        sub = U[Y0:Y0 + CH, X0:X0 + CW]; hsub = H2[Y0:Y0 + CH, X0:X0 + CW]
        res['scenes'][f'{p} {y}'] = {'displayId': SC[p][y], 'flagged_fraction_of_crop_footprint': None}
        covered = np.zeros((CH, CW), bool); covered[:] = True
        # fraction relative to the part of the crop this path covers
        reg = np.zeros_like(U, bool); reg[oy:oy + g['height'], ox:ox + g['width']] = True; rsub = reg[Y0:Y0 + CH, X0:X0 + CW]
        res['scenes'][f'{p} {y}'] = {'displayId': SC[p][y], 'path_area_in_crop_px': int(rsub.sum()), 'flagged_px': int(sub.sum()), 'flagged_fraction_of_path_area_in_crop': round(float(sub.sum() / max(rsub.sum(), 1)), 5),
                                      'high_confidence_px': int(hsub.sum()), 'largest_blobs': blobs(sub.astype(bool))}
        full |= sub; hc |= hsub
    res['scenes'][f'ALL {y}'] = {'flagged_px': int(full.sum()), 'flagged_fraction_of_crop': round(float(full.mean()), 5), 'high_confidence_px': int(hc.sum())}
    np.save(c.VIS + f'cache/cloud_{y}.npy', full)
    print(y, res['scenes'][f'ALL {y}'], flush=True)
json.dump(res, open(c.VIS + 'cloud_validation.json', 'w'), indent=1)
# overlays: 2011 display frame with flagged pixels outlined in magenta; plus enlarged crops of the biggest blobs
base = np.load(c.VIS + 'cache/TOSH_2011_base.npy'); m = np.load(c.VIS + 'cache/cloud_2011.npy').astype(bool)
ov = base.copy(); edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)); 
for dy in range(-2, 3):
    for dx in range(-2, 3): ov[np.roll(np.roll(edge, dy, 0), dx, 1)] = (255, 0, 255)
im = Image.fromarray(ov); im.thumbnail((1280, 720)); im.save(c.VIS + 'cloud_2011_overlay.jpg', quality=85)
bl = res['scenes']['TW 2011']['largest_blobs'][:3]; tiles = []
for b in bl:
    x0, y0, x1, y1 = b['bbox_x0y0x1y1_in_crop_px']; cxm, cym = (x0 + x1) // 2, (y0 + y1) // 2; xs, ys = max(0, min(CW - 400, cxm - 200)), max(0, min(CH - 400, cym - 200))
    a = Image.fromarray(base[ys:ys + 400, xs:xs + 400]); bb = Image.fromarray(ov[ys:ys + 400, xs:xs + 400]); t = Image.new('RGB', (800, 400)); t.paste(a, (0, 0)); t.paste(bb, (400, 0)); tiles.append(t)
if tiles:
    s = Image.new('RGB', (800, 400 * len(tiles)))
    for i, t in enumerate(tiles): s.paste(t, (0, 400 * i))
    s.save(c.VIS + 'cloud_2011_blob_crops.jpg', quality=88)
print('done')
