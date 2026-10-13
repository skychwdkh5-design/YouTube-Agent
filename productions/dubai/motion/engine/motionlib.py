"""OrbitalAtlas motion components (numpy + Pillow only). Reusable across scenes.
Coordinates: SOURCE pixels are in the full-resolution edge convention of the image a View looks at;
SCREEN pixels are 1920x1080. Anything defined in source pixels moves with the camera, so labels and outlines
stay on the pixels they were defined on. Nothing here knows about geography."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
Image.MAX_IMAGE_PIXELS = None
W, H, SS = 1920, 1080, 2
INK, TEXT, AMBER, CYAN, MUTED = (11, 15, 20), (234, 240, 246), (255, 194, 71), (92, 225, 230), (138, 148, 163)
_FR, _FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}
def font(size, bold=False):
    k = (size, bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(_FB if bold else _FR, size)
    return _fc[k]

# ---- easing ------------------------------------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, t0, t1): return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)
def smoother(t): t = clamp(t); return t*t*t*(t*(6*t-15)+10)
def smooth(t): t = clamp(t); return t*t*(3-2*t)
def out_cubic(t): t = clamp(t); return 1-(1-t)**3
def lerp(a, b, t): return a + (b-a)*t
def lerpv(a, b, t): return tuple(lerp(x, y, t) for x, y in zip(a, b))

# ---- image pyramid + view ----------------------------------------------------------------------------------
class Pyramid:
    def __init__(self, img):
        self.img = img; self.size = img.size
        self.levels = [(0.25, img.resize((img.width//4, img.height//4), Image.LANCZOS)),
                       (0.5, img.resize((img.width//2, img.height//2), Image.LANCZOS)), (1.0, img)]
    def render(self, crop, size):
        scale = size[0] / crop[2]
        f, im = next(((f, im) for f, im in self.levels if f >= scale*0.999), self.levels[-1])
        fx, fy = im.width/self.size[0], im.height/self.size[1]
        x, y, w, h = crop[0]*fx, crop[1]*fy, crop[2]*fx, crop[3]*fy
        box = (max(0.0, x), max(0.0, y), min(float(im.width), x+w), min(float(im.height), y+h))
        return im.resize(size, Image.LANCZOS, box=box)

class View:
    """window = screen rectangle (x, y, w, h); crop = source rectangle with the same aspect ratio."""
    def __init__(self, win, crop): self.win, self.crop = win, crop; self.k = win[2] / crop[2]
    def pt(self, p): return np.asarray(p, float) * self.k - np.array([self.crop[0]*self.k - self.win[0], self.crop[1]*self.k - self.win[1]])
    def pts(self, P): return (np.asarray(P, float) - [self.crop[0], self.crop[1]]) * self.k + [self.win[0], self.win[1]]

def make_view(win, cx, cy, ch, imgsize):
    cw = ch * win[2] / win[3]
    if cw > imgsize[0]: s = imgsize[0]/cw; cw, ch = cw*s, ch*s
    if ch > imgsize[1]: s = imgsize[1]/ch; cw, ch = cw*s, ch*s
    cx = clamp(cx, cw/2, imgsize[0]-cw/2); cy = clamp(cy, ch/2, imgsize[1]-ch/2)
    return View(win, (cx-cw/2, cy-ch/2, cw, ch))

def camera_at(t, keys, imgsize):
    """keys = [(t, win, cx, cy, ch)] ; between keys: smoother easing, log-lerp of crop height, lerp of window/centre."""
    if t <= keys[0][0]: k = keys[0]; return make_view(k[1], k[2], k[3], k[4], imgsize)
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            e = smoother(seg(t, a[0], b[0]))
            ch = math.exp(lerp(math.log(a[4]), math.log(b[4]), e))
            return make_view(lerpv(a[1], b[1], e), lerp(a[2], b[2], e), lerp(a[3], b[3], e), ch, imgsize)
    k = keys[-1]; return make_view(k[1], k[2], k[3], k[4], imgsize)

# ---- polylines ------------------------------------------------------------------------------------------------
def cumlen(p): return np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
def partial(p, cum, frac):
    """first `frac` of the polyline by arc length -> (points, head point)."""
    if frac >= 1.0: return p, p[-1]
    if frac <= 0.0 or len(p) < 2: return p[:1], p[0]
    L = cum[-1]*frac; i = min(int(np.searchsorted(cum, L, side="right")-1), len(p)-2)
    f = (L-cum[i]) / max(cum[i+1]-cum[i], 1e-9); head = p[i] + (p[i+1]-p[i])*f
    return np.vstack([p[:i+1], head]), head
def chaikin(p, n=3):
    for _ in range(n):
        q = np.empty((len(p)*2-2, 2)); q[0::2] = 0.75*p[:-1]+0.25*p[1:]; q[1::2] = 0.25*p[:-1]+0.75*p[1:]
        p = np.vstack([p[:1], q, p[-1:]])
    return p

# ---- supersampled stroke layers + glow --------------------------------------------------------------------------
class Stroke:
    """RGBA stroke layer drawn at 2x and reduced; initialised with the stroke colour so edges do not darken."""
    def __init__(self, color): self.c = color; self.im = Image.new("RGBA", (W*SS, H*SS), color+(0,)); self.d = ImageDraw.Draw(self.im, "RGBA"); self.used = False
    def line(self, pts, width=3.0, alpha=1.0):
        pts = np.asarray(pts, float)
        if len(pts) < 2 or alpha <= 0: return
        if (pts[:, 0].max() < -50) or (pts[:, 0].min() > W+50) or (pts[:, 1].max() < -50) or (pts[:, 1].min() > H+50): return
        self.d.line([tuple(q) for q in (pts*SS)], fill=self.c+(int(255*clamp(alpha)),), width=max(1, int(width*SS)), joint="curve"); self.used = True
    def dot(self, p, r=5.0, alpha=1.0):
        x, y = p[0]*SS, p[1]*SS; self.d.ellipse([x-r*SS, y-r*SS, x+r*SS, y+r*SS], fill=self.c+(int(255*clamp(alpha)),)); self.used = True
    def ring(self, p, r, width=2.0, alpha=1.0):
        x, y = p[0]*SS, p[1]*SS; self.d.ellipse([x-r*SS, y-r*SS, x+r*SS, y+r*SS], outline=self.c+(int(255*clamp(alpha)),), width=max(1, int(width*SS))); self.used = True
    def finish(self, glow=0.0, radius=6, mask=None):
        if not self.used: return None
        small = self.im.reduce(SS)
        if mask is not None: small.putalpha(ImageChops.multiply(small.getchannel("A"), mask))
        if glow > 0:
            g = small.filter(ImageFilter.GaussianBlur(radius)); g.putalpha(g.getchannel("A").point(lambda v: int(min(255, v*glow*2.2))))
            return Image.alpha_composite(g, small)
        return small

def window_mask(win):
    m = Image.new("L", (W, H), 0); x, y, w, h = win; ImageDraw.Draw(m).rectangle([int(round(x)), int(round(y)), int(round(x+w))-1, int(round(y+h))-1], fill=255); return m

# ---- text ----------------------------------------------------------------------------------------------------
UIREG = []     # (group, x0, y0, x1, y1, alpha) of text and plates drawn this frame, for collision QA
def ui_reset(): UIREG.clear()
def text_kinetic(layer, xy, s, fnt, fill, t, t0, per=0.028, dur=0.40, rise=16, track=0.0, out_t=None, out_dur=0.25, shadow=False, group=None):
    """per-character reveal: each glyph fades and rises with ease-out; optional fade-out from out_t."""
    d = ImageDraw.Draw(layer, "RGBA"); x, y = xy; xs = 0.0; amax = 0.0
    for i, ch in enumerate(s):
        a = out_cubic(seg(t, t0+i*per, t0+i*per+dur))
        if out_t is not None: a *= 1 - smooth(seg(t, out_t+i*0.01, out_t+i*0.01+out_dur))
        amax = max(amax, a)
        if a > 0.003:
            if shadow: d.text((x+xs+2, y + rise*(1-a)+2), ch, font=fnt, fill=(0, 0, 0, int(170*a)))
            d.text((x+xs, y + rise*(1-a)), ch, font=fnt, fill=fill+(int(255*a),))
        xs += fnt.getlength(ch) + track
    if group is not None and amax > 0.35: UIREG.append((group, x, y, x+xs, y+fnt.size*1.25, amax))
    return xs
def text_width(s, fnt, track=0.0): return sum(fnt.getlength(c)+track for c in s)
def chip(layer, xy, s, fnt, t, t0, out_t=None, accent=AMBER, pad=14, group=None):
    """lower-third style chip: accent bar, translucent plate that grows, text fades in."""
    a_in = out_cubic(seg(t, t0, t0+0.45)); a = a_in * (1 - (smooth(seg(t, out_t, out_t+0.3)) if out_t is not None else 0))
    if a <= 0.003: return
    x, y = xy; w = text_width(s, fnt) + pad*2 + 8; h = fnt.size + pad*1.4
    d = ImageDraw.Draw(layer, "RGBA"); ww = w*out_cubic(seg(t, t0, t0+0.5))
    if group is not None and a > 0.35: UIREG.append((group, x, y, x+w, y+h, a))
    d.rectangle([x, y, x+ww, y+h], fill=(0, 0, 0, int(150*a)))
    d.rectangle([x, y, x+4, y+h], fill=accent+(int(255*a),))
    d.text((x+pad+8, y+pad*0.55), s, font=fnt, fill=TEXT+(int(255*a_in*(a/max(a_in, 1e-6))),))

# ---- background and depth -----------------------------------------------------------------------------------
_vig = None
def vignette():
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H//4, 0:W//4]; r = np.hypot((xx-W/8)/(W/8), (yy-H/8)/(H/8))
        _vig = Image.fromarray((np.clip(1-0.34*np.clip(r-0.55, 0, 1)**1.5, 0.6, 1)*255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return _vig
def depth_background(pyr, view, dark=0.15):
    """blurred, darkened, enlarged view of the SAME image behind the window (depth cue; not data)."""
    cx, cy = view.crop[0]+view.crop[2]/2, view.crop[1]+view.crop[3]/2
    ch = min(view.crop[3]*1.6, pyr.size[1]); cw = ch*16/9
    if cw > pyr.size[0]: cw = pyr.size[0]; ch = cw*9/16
    cx = clamp(cx, cw/2, pyr.size[0]-cw/2); cy = clamp(cy, ch/2, pyr.size[1]-ch/2)
    s = pyr.render((cx-cw/2, cy-ch/2, cw, ch), (480, 270)).filter(ImageFilter.GaussianBlur(10))
    a = np.asarray(s, np.float32)*dark + np.array(INK, np.float32)*0.5
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
def window_shadow(base, win, strength=0.65):
    m = Image.new("L", (W//4, H//4), 0); x, y, w, h = [v/4 for v in win]
    ImageDraw.Draw(m).rectangle([x+3, y+7, x+w+3, y+h+7], fill=int(255*strength)); m = m.filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BICUBIC)
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), base, m)


# ---- v2: spline camera, overscan paste, motion blur helpers, markers -----------------------------------------------
def _pchip(ts, ys):
    n = len(ts); h = np.diff(ts); d = np.diff(ys)/h; m = np.zeros(n)
    for k in range(1, n-1):
        if d[k-1]*d[k] > 0:
            w1, w2 = 2*h[k]+h[k-1], h[k]+2*h[k-1]; m[k] = (w1+w2)/(w1/d[k-1]+w2/d[k])
    return m
class SplineCam:
    """Full-screen 16:9 camera through keys (t, cx, cy, ch). Monotone cubic (PCHIP) per channel: velocity is continuous,
    no overshoot, rest only at the first and last key and at true turning points. Crop height is interpolated in log space."""
    def __init__(self, keys, imgsize, overscan=1.15):
        self.ts = np.array([k[0] for k in keys], float); self.size = imgsize; self.over = overscan
        self.ch = [np.array([k[i] if i < 3 else math.log(k[3]) for k in keys], float) for i in (1, 2, 3)]
        self.m = [_pchip(self.ts, y) for y in self.ch]
    def _h(self, t, y, m):
        t = min(max(t, self.ts[0]), self.ts[-1]); i = min(int(np.searchsorted(self.ts, t, side="right")-1), len(self.ts)-2)
        h = self.ts[i+1]-self.ts[i]; s = (t-self.ts[i])/h
        return ((2*s**3-3*s**2+1)*y[i] + (s**3-2*s**2+s)*h*m[i] + (-2*s**3+3*s**2)*y[i+1] + (s**3-s**2)*h*m[i+1])
    def raw(self, t): return tuple(self._h(t, y, m) for y, m in zip(self.ch, self.m))
    def view(self, t):
        cx, cy, lch = self.raw(t); ch = math.exp(lch); W0, H0 = self.size
        cw = ch*16/9
        if cw > W0*self.over: s = W0*self.over/cw; cw, ch = cw*s, ch*s
        if ch > H0: s = H0/ch; cw, ch = cw*s, ch*s
        cy = clamp(cy, ch/2, H0-ch/2); cx = clamp(cx, cw/2, W0-cw/2) if cw <= W0 else W0/2
        return View((0.0, 0.0, float(W), float(H)), (cx-cw/2, cy-ch/2, cw, ch))
    def speed(self, t, dt=1/60):
        a, b = self.view(t-dt), self.view(t+dt)
        return (np.hypot(*(b.pts([[0, 0]])[0] - a.pts([[0, 0]])[0])) + abs(math.log(b.crop[3]/a.crop[3]))*700) / (2*dt*30)   # screen px per frame

def paste_image(base, pyr, view, feather=150):
    """paste the part of the image inside the view; where the view runs past the image, the edge is feathered (not faked)."""
    x, y, w, h = view.crop; k = view.k; Wi, Hi = pyr.size
    x0, y0, x1, y1 = max(0.0, x), max(0.0, y), min(float(Wi), x+w), min(float(Hi), y+h)
    dx0, dy0, dx1, dy1 = int(round((x0-x)*k)), int(round((y0-y)*k)), int(round((x1-x)*k)), int(round((y1-y)*k))
    dx1, dy1 = min(dx1, W), min(dy1, H)
    patch = pyr.render((x0, y0, x1-x0, y1-y0), (dx1-dx0, dy1-dy0))
    m = np.ones((dy1-dy0, dx1-dx0), np.float32)
    if x0 > x and dx1-dx0 > 2*feather: m[:, :feather] *= np.linspace(0, 1, feather)[None, :]
    if x1 < x+w and dx1-dx0 > 2*feather: m[:, -feather:] *= np.linspace(1, 0, feather)[None, :]
    if y0 > y and dy1-dy0 > 2*feather: m[:feather, :] *= np.linspace(0, 1, feather)[:, None]
    if y1 < y+h and dy1-dy0 > 2*feather: m[-feather:, :] *= np.linspace(1, 0, feather)[:, None]
    base.paste(patch, (dx0, dy0), Image.fromarray((m*255).astype(np.uint8)))
    return base

def brackets(stroke, r, arm=22.0, width=2.0, alpha=1.0, prog=1.0):
    """four corner brackets around screen rect r=(x0,y0,x1,y1); prog 0..1 grows the arms."""
    x0, y0, x1, y1 = r; a = arm*clamp(prog)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1)):
        stroke.line([(cx+sx*a, cy), (cx, cy), (cx, cy+sy*a)], width, alpha)
def crosshair(stroke, p, r=15.0, width=2.0, alpha=1.0, tick=11.0):
    stroke.ring(p, r, width, alpha)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): stroke.line([(p[0]+dx*(r-3), p[1]+dy*(r-3)), (p[0]+dx*(r+tick), p[1]+dy*(r+tick))], width, alpha)

def title_plate(layer, xy, s, fnt, t, t0, out_t=None, accent=AMBER, pad=18, group=None):
    """large title on a translucent plate: plate grows, glyphs rise and fade in, whole plate fades out."""
    a_in = out_cubic(seg(t, t0, t0+0.5)); a = a_in * (1 - (smooth(seg(t, out_t, out_t+0.3)) if out_t is not None else 0))
    if a <= 0.003: return
    x, y = xy; w = text_width(s, fnt, 2) + pad*2 + 6; h = fnt.size + pad*1.3
    d = ImageDraw.Draw(layer, "RGBA"); ww = w*out_cubic(seg(t, t0, t0+0.55))
    if group is not None and a > 0.35: UIREG.append((group, x, y, x+w, y+h, a))
    d.rectangle([x, y, x+ww, y+h], fill=(0, 0, 0, int(165*a))); d.rectangle([x, y, x+5, y+h], fill=accent+(int(255*a),))
    text_kinetic(layer, (x+pad+6, y+pad*0.55), s, fnt, TEXT, t, t0+0.12, per=0.022, track=2, out_t=out_t, out_dur=0.3)
