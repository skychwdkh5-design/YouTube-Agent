"""ATLAS face rig on the body's own (calm, matching-angle) head.

Works at 3x of reference-sheet scale. Per frame it takes continuous controls
  open (0..1), width (0.75..1.1), blink (0..1), brow (-1..1), smile (0..1)
and returns an RGBA head image whose top-left sits at sheet coords HEAD_TL with scale 1/3.
The open mouth interior is the painted one from the 'Speaking' head, transplanted and
scaled, so teeth and lips stay in the sheet's painting style.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

K = 3
BG = np.array([234, 224, 220], np.float32)
HEAD_TL = (880, 36)
HEAD_BR = (986, 123)
CEN, RAD = (932.5, 90.0), 49.5

# landmarks on the body head (sheet px)
MOUTH_L, MOUTH_R = np.array([940.0, 95.4]), np.array([955.2, 93.6])
EYE_N = (935.6, 78.6, 943.4, 82.6)       # near eye box
EYE_F = (951.4, 78.2, 955.8, 82.2)       # far eye box
BROW = (932.0, 69.5, 957.5, 76.5)        # both brows
JAW = (928.0, 95.0, 960.0, 113.0)        # chin / lower face that drops with the jaw
# the open mouth on the 'Speaking' head (sheet px)
SP_L, SP_R = np.array([356.0, 665.0]), np.array([387.5, 656.0])
SP_BOX = (348, 648, 396, 678)
SP_POLY = [(355, 664), (372, 659), (387, 655), (389, 660), (384, 667), (372, 670), (358, 669)]


def _to3(p):
    return ((p[0] - HEAD_TL[0]) * K, (p[1] - HEAD_TL[1]) * K)


class Face:
    def __init__(self, ref_path, glass=True):
        src = Image.open(ref_path).convert('RGB')
        self.src = np.asarray(src).astype(np.float32)
        x0, y0 = HEAD_TL
        x1, y1 = HEAD_BR
        crop = src.crop((x0, y0, x1, y1))
        big = crop.resize(((x1 - x0) * K, (y1 - y0) * K), Image.LANCZOS)
        rgb = np.asarray(big).astype(np.float32)
        # glass alpha inside the bubble, opaque head/hair
        h, w = rgb.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        sx, sy = xx / K + x0, yy / K + y0
        r = np.sqrt((sx - CEN[0]) ** 2 + (sy - CEN[1]) ** 2)
        inside = r < RAD
        d = np.abs(rgb - BG).max(-1)
        if glass:
            alpha = np.where(inside, np.clip(0.16 + d / 70, 0, 1), 0.0)
        else:
            # head only (new helmet is a separate layer): keep painted hair/skin, drop glass
            alpha = np.where(inside, np.clip((d - 34) / 22, 0, 1), 0.0)
            am = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))
            alpha = np.asarray(am).astype(np.float32) / 255
        alpha *= np.clip(RAD + 0.5 - r, 0, 1)
        alpha *= np.clip((117.0 - sy) / 4.0, 0, 1)
        rgb = np.where(alpha[..., None] > 0, BG + (rgb - BG) / np.maximum(alpha[..., None], 1e-3), rgb)
        self.rgb = np.clip(rgb, 0, 255)
        self.alpha = alpha
        self.h, self.w = h, w
        self.yy, self.xx = yy, xx
        self._mouth_patch()
        self._skin = self._sample((939, 76.5))
        self._lidc = self._sample((940.5, 84.8)) * 0.93

    def _sample(self, p):
        x, y = _to3(p)
        return self.rgb[int(y) - 2:int(y) + 3, int(x) - 2:int(x) + 3].reshape(-1, 3).mean(0)

    # ---------------------------------------------------------------- mouth
    def _mouth_patch(self):
        bx0, by0, bx1, by1 = SP_BOX
        patch = self.src[by0:by1, bx0:bx1].copy()
        m = Image.new('L', (bx1 - bx0, by1 - by0), 0)
        ImageDraw.Draw(m).polygon([(x - bx0, y - by0) for x, y in SP_POLY], fill=255)
        poly = np.asarray(m) > 127
        skin = np.array([214, 150, 112], np.float32)
        lum = patch.mean(-1)
        open_ = poly & ((np.abs(patch - skin).max(-1) > 48) | (lum < 120))
        a = Image.fromarray((open_ * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
        alpha = np.asarray(a).astype(np.float32) / 255 * poly
        # match the body head's lighter, softer painting
        patch = patch * 0.92 + 12
        self.mp = Image.fromarray(np.dstack([np.clip(patch, 0, 255), alpha * 255]).astype(np.uint8), 'RGBA')
        # seam (centre line) of the opening, in patch px
        ys, xs = np.nonzero(open_)
        self.mp_seam_c = np.array([xs.mean(), ys.mean()])
        self.mp_L = SP_L - (bx0, by0)
        self.mp_R = SP_R - (bx0, by0)

    def _paste_mouth(self, img, open_, width, smile):
        """Affine-map the painted opening between the mouth corners, scaled by open/width."""
        L3, R3 = np.array(_to3(MOUTH_L)), np.array(_to3(MOUTH_R))
        dst_c = (L3 + R3) / 2 + np.array([0, -smile * 1.2 * K * 0.3])
        dst_v = R3 - L3
        src_v = self.mp_R - self.mp_L
        s = np.hypot(*dst_v) / np.hypot(*src_v) * width
        ang = np.arctan2(dst_v[1], dst_v[0]) - np.arctan2(src_v[1], src_v[0])
        c, si = np.cos(ang), np.sin(ang)
        # source frame: u along the mouth, v across it; v is scaled by open
        u = src_v / np.hypot(*src_v)
        v = np.array([-u[1], u[0]])
        sc = (self.mp_L + self.mp_R) / 2
        # build forward matrix src->dst: dst = dst_c + s*R*(A*(p-sc)), A scales v by open
        A = np.outer(u, u) + max(open_, 0.02) * 1.9 * np.outer(v, v)
        Rm = np.array([[c, -si], [si, c]])
        M = s * Rm @ A
        Minv = np.linalg.inv(M)
        off = sc - Minv @ dst_c
        tile = self.mp.transform((self.w, self.h), Image.AFFINE,
                                 (Minv[0, 0], Minv[0, 1], off[0], Minv[1, 0], Minv[1, 1], off[1]),
                                 Image.BILINEAR)
        t = np.asarray(tile).astype(np.float32)
        a = t[..., 3:4] / 255 * min(1.0, open_ * 4)
        return img * (1 - a) + t[..., :3] * a

    # ---------------------------------------------------------------- warps
    def _shift(self, img, box, dy, feather=2.0):
        """Shift a soft-edged region vertically by dy sheet px (bilinear)."""
        if abs(dy) < 1e-3:
            return img
        x0, y0, x1, y1 = [v * K for v in (box[0] - HEAD_TL[0], box[1] - HEAD_TL[1], box[2] - HEAD_TL[0], box[3] - HEAD_TL[1])]
        f = feather * K
        wx = np.clip(np.minimum(self.xx - x0, x1 - self.xx) / f, 0, 1)
        wy = np.clip(np.minimum(self.yy - y0, y1 - self.yy) / f, 0, 1)
        wgt = (wx * wy) ** 1.0
        sy = self.yy - dy * K * wgt
        y0i = np.clip(np.floor(sy).astype(int), 0, self.h - 2)
        fy = np.clip(sy - y0i, 0, 1)[..., None]
        xi = self.xx.astype(int)
        return img[y0i, xi] * (1 - fy) + img[y0i + 1, xi] * fy

    def _eyelid(self, img, box, b):
        if b <= 0.02:
            return img
        x0, y0, x1, y1 = [(box[0] - HEAD_TL[0]) * K, (box[1] - HEAD_TL[1]) * K, (box[2] - HEAD_TL[0]) * K, (box[3] - HEAD_TL[1]) * K]
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 * 0.9, (y1 - y0) / 2 * 0.95
        inside = ((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2 < 1
        lid_y = y0 + (y1 - y0) * b
        cover = inside & (self.yy < lid_y)
        m = Image.fromarray((cover * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
        m = np.asarray(m).astype(np.float32)[..., None] / 255
        out = img * (1 - m) + self._lidc * m
        # lash line at the lid edge
        lash = inside & (np.abs(self.yy - lid_y) < 1.6)
        lm = Image.fromarray((lash * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
        lm = np.asarray(lm).astype(np.float32)[..., None] / 255 * min(1, b * 2.5)
        return out * (1 - lm * 0.85) + np.array([45, 30, 26], np.float32) * lm * 0.85

    def render(self, open_=0.0, width=1.0, blink=0.0, brow=0.0, smile=0.0):
        img = self.rgb
        img = self._shift(img, BROW, -brow * 1.3, 2.5)
        img = self._shift(img, JAW, open_ * 2.6, 3.0)
        if open_ > 0.03:
            img = self._paste_mouth(img, open_, width, smile)
        img = self._eyelid(img, EYE_N, blink)
        img = self._eyelid(img, EYE_F, blink)
        rgba = np.dstack([np.clip(img, 0, 255), self.alpha * 255]).astype(np.uint8)
        return Image.fromarray(rgba, 'RGBA')
