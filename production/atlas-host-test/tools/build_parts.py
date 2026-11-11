"""Cut ATLAS cutout-rig parts from the approved reference sheet.

All coordinates are in reference-sheet pixels (1536x1024). Output: RGBA parts
in parts/ plus parts/rig.json with pivots, all in the 3/4 body's local frame.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REF = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
src = np.asarray(Image.open(REF).convert('RGB')).astype(np.float32)
BG = np.array([234, 224, 220], np.float32)
H, W = src.shape[:2]


def dist_bg(a):
    return np.abs(a - BG).max(-1)


def flood_bg(box, tol=15):
    """Background = paper-coloured regions: touching the border, or enclosed and >= 25 px."""
    x0, y0, x1, y1 = box
    a = src[y0:y1, x0:x1]
    ok = dist_bg(a) < tol
    big = big_components(ok, 8)
    seed = np.zeros_like(ok)
    seed[0, :] = seed[-1, :] = seed[:, 0] = seed[:, -1] = True
    m = seed & ok
    while True:
        n = m.copy()
        n[1:] |= m[:-1]; n[:-1] |= m[1:]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        n &= ok
        if (n == m).all():
            break
        m = n
    return m | big


def big_components(ok, min_px):
    h, w = ok.shape
    seen = np.zeros_like(ok)
    out = np.zeros_like(ok)
    for y in range(h):
        for x in range(w):
            if ok[y, x] and not seen[y, x]:
                stack = [(y, x)]; seen[y, x] = True; comp = []
                while stack:
                    cy, cx = stack.pop(); comp.append((cy, cx))
                    for ny, nx in ((cy+1, cx), (cy-1, cx), (cy, cx+1), (cy, cx-1)):
                        if 0 <= ny < h and 0 <= nx < w and ok[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; stack.append((ny, nx))
                if len(comp) >= min_px:
                    ys, xs = zip(*comp); out[list(ys), list(xs)] = True
    return out


def poly_mask(box, poly):
    x0, y0, x1, y1 = box
    im = Image.new('L', (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(im).polygon([(x - x0, y - y0) for x, y in poly], fill=255)
    return np.asarray(im) > 127


def inpaint(rgb, hole, iters=400):
    """Simple diffusion fill of hole pixels from their neighbours."""
    out = rgb.copy()
    known = ~hole
    out[hole] = out[known].mean(0)
    for _ in range(iters):
        p = np.pad(out, ((1, 1), (1, 1), (0, 0)), mode='edge')
        avg = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 4
        out[hole] = avg[hole]
    # a little painted grain so fills are not flat
    rng = np.random.default_rng(3)
    out[hole] += rng.normal(0, 4, out[hole].shape)
    return out


def save(name, rgb, alpha, box):
    x0, y0, x1, y1 = box
    solid = alpha > 0.5
    keep = big_components(solid, 40)
    grow = keep.copy(); grow[1:] |= keep[:-1]; grow[:-1] |= keep[1:]; grow[:, 1:] |= keep[:, :-1]; grow[:, :-1] |= keep[:, 1:]
    alpha = alpha * grow
    if not name.startswith('head'):
        # defringe: pull 1 px in and replace edge colours with interior colours (no paper halo)
        a = alpha.copy()
        er = a.copy()
        er[1:] = np.minimum(er[1:], a[:-1]); er[:-1] = np.minimum(er[:-1], a[1:])
        er[:, 1:] = np.minimum(er[:, 1:], a[:, :-1]); er[:, :-1] = np.minimum(er[:, :-1], a[:, 1:])
        alpha = 0.35 * a + 0.65 * er
        rgb = rgb.copy()
        inner = er > 0.95
        lum = rgb.mean(-1); sat = rgb.max(-1) - rgb.min(-1)
        paperish = (np.abs(rgb - BG).max(-1) < 22)
        for _ in range(3):
            edge = (alpha > 0) & ~inner
            acc = np.zeros_like(rgb); cnt = np.zeros(rgb.shape[:2])
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                sh_in = np.roll(np.roll(inner, dy, 0), dx, 1)
                sh_rgb = np.roll(np.roll(rgb, dy, 0), dx, 1)
                acc += sh_rgb * sh_in[..., None]; cnt += sh_in
            fix = edge & (cnt > 0) & (paperish | (alpha < 0.9))
            rgb[fix] = acc[fix] / cnt[fix][:, None]
            inner = inner | fix
        alpha = alpha * ~(paperish & (alpha < 0.999) & ~inner)
    a = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), a]), 'RGBA')
    bb = im.getbbox()
    im = im.crop(bb)
    im.save(f'{OUT}/{name}.png')
    return [x0 + bb[0], y0 + bb[1]]  # sheet-space top-left of saved part


def soften(mask):
    im = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    return np.asarray(im).astype(np.float32) / 255


rig = {'parts': {}, 'pivots': {}}

# ---------------------------------------------------------------- 3/4 body
BOX = (856, 28, 1030, 497)
x0, y0, x1, y1 = BOX
body = src[y0:y1, x0:x1].copy()
fg = ~flood_bg(BOX)
yy, xx = np.mgrid[y0:y1, x0:x1]
# drop the ground shadow under the boots
sat = body.max(-1) - body.min(-1)
fg &= ~((yy > 482) & (body.mean(-1) > 125) & (sat < 40))
# drop the original head inside the helmet (replaced by the speaking head)
head_hole = ((xx - 932) ** 2 + (yy - 90) ** 2 < 52 ** 2) & (yy < 110)
fg &= ~head_hole
fg &= ~(yy < 108)
fg &= ~((yy < 100) & (xx > 958))
fg &= ~((yy < 140) & (body.mean(-1) > 185) & ((body.max(-1) - body.min(-1)) < 35))

P = lambda poly: poly_mask(BOX, poly) & fg

near_upper = P([(864, 124), (896, 118), (913, 134), (912, 192), (904, 214), (866, 220), (862, 150)])
near_fore = P([(864, 212), (905, 206), (904, 262), (868, 266)])
near_hand = P([(866, 262), (906, 258), (912, 330), (868, 330)]) & ~poly_mask(BOX, [(906, 262), (930, 262), (930, 330), (906, 330)])
# pouch pixels sit right of the glove; keep the glove only (dark pixels + its outline)
far_upper = P([(983, 158), (1003, 168), (1008, 246), (985, 246)])
far_fore = P([(985, 240), (1010, 240), (1013, 270), (988, 270)])
far_hand = P([(986, 266), (1026, 266), (1026, 322), (986, 322)])
YCUT = 280  # torso keeps everything above this line
near_thigh = P([(866, 262), (938, 262), (944, 340), (930, 372), (870, 378)]) & ~near_hand
far_thigh = P([(936, 262), (994, 262), (994, 372), (942, 372), (944, 340)])
near_shin = P([(866, 356), (934, 356), (934, 452), (868, 452)])
far_shin = P([(934, 356), (996, 356), (990, 452), (936, 452)])
near_foot = P([(860, 440), (938, 440), (940, 497), (860, 497)])
far_foot = P([(934, 440), (1026, 440), (1026, 497), (934, 497)])

arms = near_upper | near_fore | near_hand | far_upper | far_fore | far_hand
torso = fg & ~arms & (yy < YCUT + 12)
# the torso keeps the pelvis band; thighs are drawn behind it
torso &= ~((yy >= YCUT) & ~poly_mask(BOX, [(890, 280), (990, 280), (985, 292), (895, 292)]))

# fill the torso where the arms used to overlap it, so raised arms reveal suit, not paper
hole_near = near_upper & poly_mask(BOX, [(900, 120), (920, 120), (920, 215), (900, 215)])
hole_far = far_upper & poly_mask(BOX, [(980, 158), (992, 158), (992, 246), (980, 246)])
body_fill = inpaint(body, hole_near | hole_far)
torso_a = soften(torso | hole_near | hole_far) * (torso | hole_near | hole_far | (soften(torso) > 0.01))

def add(name, mask, rgb=body):
    tl = save(name, rgb, soften(mask) * (soften(mask) > 0.02), BOX)
    rig['parts'][name] = {'tl': tl}

add('torso', torso | hole_near, body_fill)
# thighs: fill their own top under the torso so rotation never shows a gap
thigh_fill = inpaint(body, poly_mask(BOX, [(870, 262), (994, 262), (994, 275), (870, 275)]) & ~fg)
add('near_upper', near_upper)
add('near_fore', near_fore)
add('near_hand', near_hand)
add('far_upper', far_upper)
add('far_fore', far_fore)
add('far_hand', far_hand)
pouch_fill = inpaint(body, near_hand & poly_mask(BOX, [(893, 270), (912, 270), (912, 330), (893, 330)]))
add('near_thigh', near_thigh | (near_hand & poly_mask(BOX, [(897, 270), (912, 270), (912, 330), (897, 330)])), pouch_fill)
add('far_thigh', far_thigh)
add('near_shin', near_shin & ~near_thigh)
add('far_shin', far_shin & ~far_thigh)
add('near_foot', near_foot & ~near_shin)
add('far_foot', far_foot & ~far_shin)

rig['pivots'] = {
    'neck': [921, 120],
    'near_shoulder': [889, 140], 'near_elbow': [885, 212], 'near_wrist': [887, 264],
    'far_shoulder': [990, 172], 'far_elbow': [997, 243], 'far_wrist': [1002, 268],
    'near_hip': [905, 270], 'near_knee': [898, 366], 'near_ankle': [895, 448],
    'far_hip': [962, 272], 'far_knee': [968, 366], 'far_ankle': [962, 448],
    'ground': 492,
}

# ---------------------------------------------------------------- heads
def head(name, box, centre, r):
    x0, y0, x1, y1 = box
    a = src[y0:y1, x0:x1].copy()
    yy, xx = np.mgrid[y0:y1, x0:x1]
    inside = (xx - centre[0]) ** 2 + (yy - centre[1]) ** 2 < r ** 2
    d = dist_bg(a)
    solid = ~flood_bg(box, 14) & ~inside
    # glass: weak alpha plus whatever paint differs from the paper
    alpha = np.where(inside, np.clip(0.16 + d / 70, 0, 1), 0)
    alpha = np.maximum(alpha, solid & (yy < centre[1] + r + 4))
    # un-premultiply the paper colour out of the glass so it reads on dark footage
    rgb = np.where(alpha[..., None] > 0, BG + (a - BG) / np.maximum(alpha[..., None], 1e-3), a)
    rgb = np.where((alpha >= 0.999)[..., None], a, rgb)
    edge = np.clip((r + 1 - np.sqrt((xx - centre[0]) ** 2 + (yy - centre[1]) ** 2)), 0, 1)
    alpha = np.where(inside | (edge > 0), np.maximum(alpha * edge, alpha * inside), alpha)
    return rgb, alpha

# speaking head (3/4 right, same turn as the body)
HB = (252, 552, 434, 708)
rgb, al = head('speak', HB, (343, 638), 86)
yyh = np.mgrid[HB[1]:HB[3], HB[0]:HB[2]][0]
xxh = np.mgrid[HB[1]:HB[3], HB[0]:HB[2]][1]
al = al * (yyh < 702) * (((xxh - 343) ** 2 + (yyh - 638) ** 2) < 88 ** 2)
rig['parts']['head_src'] = {'box': HB, 'centre': [343, 638], 'r': 86}

# mouth visemes: closed / mid / open, built from the open mouth on the speaking head
MB = (350, 650, 394, 676)
m_open = (dist_bg(src) > 0)  # placeholder full-size mask
mx0, my0, mx1, my1 = MB
mouth = src[my0:my1, mx0:mx1]
lum = mouth.mean(-1)
skin = np.array([214, 150, 112], np.float32)
not_skin = (np.abs(mouth - skin).max(-1) > 48)
# the opening: dark gap + teeth, inside the lip outline
lip_poly = poly_mask(MB, [(355, 664), (372, 659), (387, 655), (389, 660), (384, 667), (372, 670), (358, 669)])
opening = lip_poly & (not_skin | (lum < 120))
_d = opening.copy(); _d[1:] |= opening[:-1]; _d[:-1] |= opening[1:]; _d[:, 1:] |= opening[:, :-1]; _d[:, :-1] |= opening[:, 1:]
opening = _d & lip_poly
_ys, _xs = np.nonzero(opening)
SEAM = np.polyfit(_xs, _ys, 1)
def mouth_variant(k):
    out = rgb.copy()
    ox, oy = mx0 - HB[0], my0 - HB[1]
    region = out[oy:oy + (my1 - my0), ox:ox + (mx1 - mx0)]
    closed = inpaint(region.copy(), opening, 300)
    # lip line along the centre of the opening
    res = closed.copy()
    if k > 0:
        hh, ww = opening.shape
        yg, xg = np.mgrid[0:hh, 0:ww].astype(np.float32)
        yc = SEAM[0] * xg + SEAM[1]
        sy = yc + (yg - yc) / k
        y0i = np.clip(np.floor(sy).astype(int), 0, hh - 2); fy = np.clip(sy - y0i, 0, 1)[..., None]
        xi = xg.astype(int)
        src_open = region.copy(); om = opening.astype(np.float32)[..., None]
        col = src_open[y0i, xi] * (1 - fy) + src_open[y0i + 1, xi] * fy
        msk = om[y0i, xi] * (1 - fy) + om[y0i + 1, xi] * fy
        msk = msk * ((sy >= 0) & (sy <= hh - 1))[..., None]
        res = res * (1 - msk) + col * msk
    # soft lip seam along the fitted centre line of the opening, fading at the corners
    if k < 0.7:
        xs = np.unique(np.nonzero(opening)[1]); xa, xb = xs.min(), xs.max()
        hh = res.shape[0]
        for x in range(xa, xb + 1):
            yc = SEAM[0] * x + SEAM[1]
            t = min(x - xa, xb - x) / max(1, (xb - xa) / 4)
            w = (1 - k / 0.7) * min(1, t) * 0.6
            for y in range(hh):
                f = max(0.0, 1 - abs(y - yc) / 1.2) * w
                res[y, x] = res[y, x] * (1 - f) + np.array([95, 45, 38]) * f
    region[:] = res
    return out

for nm, k in [('mouth_closed', 0.0), ('mouth_mid', 0.5), ('mouth_open', 1.0)]:
    v = mouth_variant(k)
    tl = save('head_' + nm, v, al, HB)
    rig['parts']['head_' + nm] = {'tl': tl}

# ---------------------------------------------------------------- hand props
PB = (896, 640, 962, 722)
pa = src[PB[1]:PB[3], PB[0]:PB[2]]
pm = ~flood_bg(PB, 15) & poly_mask(PB, [(896, 640), (962, 640), (962, 716), (896, 716)])
tl = save('hand_point', pa, soften(pm), PB)
rig['parts']['hand_point'] = {'tl': tl}

RB = (1418, 684, 1504, 800)
ra = src[RB[1]:RB[3], RB[0]:RB[2]]
rpoly = [(1428, 700), (1450, 688), (1476, 690), (1492, 702), (1503, 730), (1503, 798), (1452, 798), (1446, 760), (1432, 748), (1424, 726)]
rm = ~flood_bg(RB, 15) & poly_mask(RB, rpoly)
tl = save('hand_rock', ra, soften(rm), RB)
rig['parts']['hand_rock'] = {'tl': tl}

json.dump(rig, open(f'{OUT}/rig.json', 'w'), indent=1)
print('ok', list(rig['parts']))
