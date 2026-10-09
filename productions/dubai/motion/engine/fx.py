"""Geographic motion-graphics effects built on motionlib (numpy + Pillow).
Every effect is anchored in SOURCE pixels of the image it sits on, so it moves with the camera:
  masks (land / sea highlights computed from the image's own pixels), wipes grown from an anchor, rotated anchored typography,
  rolling year digits, comet trails, spotlight dimming. Nothing here knows geography or claims registration."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from motionlib import *

# ---- masks computed from the image itself -------------------------------------------------------------------------
def land_mask(arr, channel="r", thresh=85):
    """bool land mask: the chosen channel (r or max), lightly box-blurred, at or above thresh."""
    a = arr[:, :, 0] if channel == "r" else arr.max(axis=2)
    g = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.BoxBlur(1))
    return np.asarray(g) >= thresh

def disc(shape, c, r):
    yy, xx = np.ogrid[:shape[0], :shape[1]]; return (xx-c[0])**2 + (yy-c[1])**2 <= r*r

def rot_mask(m):
    """90 degrees clockwise, matching PIL's ROTATE_270 used for the displayed images."""
    return np.rot90(m, k=-1)

class MaskLayer:
    """L-mode mask image pyramid; renders the camera's crop at screen size as float 0..1."""
    def __init__(self, mask_bool, size):
        im = Image.fromarray((mask_bool*255).astype(np.uint8)); assert im.size == size, (im.size, size); self.pyr = Pyramid(im); self.size = size
    def at(self, view):
        return np.asarray(self.pyr.render(view.crop, (W, H)), np.float32)/255.0

def smoothstep01(x): x = np.clip(x, 0, 1); return x*x*(3-2*x)

def highlight(frame_rgba, mask_arr, color, alpha, view=None, anchor_px=None, radius_px=None, feather=70.0):
    """tint the masked pixels; optional radial wipe from anchor_px (screen px) with current radius radius_px."""
    if alpha <= 0.003: return frame_rgba
    m = mask_arr
    if radius_px is not None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.hypot(xx-anchor_px[0], yy-anchor_px[1])
        m = m * smoothstep01((radius_px - d)/feather + 0.0)
    a = (m*alpha*255).astype(np.uint8); ov = Image.new("RGBA", (W, H), tuple(color)+(0,)); ov.putalpha(Image.fromarray(a))
    return Image.alpha_composite(frame_rgba, ov)

def spotlight(frame_rgb, center, radius, strength, feather=220.0):
    """dim everything outside a soft disc (focus cue). strength 0..1 is the maximum dimming."""
    if strength <= 0.003: return frame_rgb
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.hypot(xx-center[0], yy-center[1])
    k = 1 - strength*smoothstep01((d-radius)/feather); a = np.asarray(frame_rgb, np.float32)*k[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# ---- typography anchored to the image -------------------------------------------------------------------------------
_tf = {}
def tfont(px, bold=True):
    px = int(max(10, round(px)))
    if (px, bold) not in _tf: _tf[(px, bold)] = font(px, bold)
    return _tf[(px, bold)]

def anchored_text(ui, view, p_src, text, size_src, t, t0, color=TEXT, track=0.0, angle=0.0, dur=0.45, per=0.05, rise=0.32,
                  out_t=None, out_dur=0.35, min_px=34, max_px=240, shadow=True, group=None, anchor="center", glow=None):
    """letters rise and fade in one by one, text lies on the image: position and size follow the camera.
    size_src = cap height of the text in SOURCE pixels; angle in degrees, counter-clockwise on screen."""
    px = clamp(size_src*view.k, min_px, max_px); f = tfont(px); ts = px*track
    adv = [f.getlength(c)+ts for c in text]; Wt = sum(adv); pad = int(px*0.6); Ht = int(px*1.5)
    tile = Image.new("RGBA", (int(Wt)+2*pad, Ht+2*pad), (0, 0, 0, 0)); d = ImageDraw.Draw(tile, "RGBA")
    sh = Image.new("RGBA", tile.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh, "RGBA"); x = pad; amax = 0.0
    for i, c in enumerate(text):
        a = out_cubic(seg(t, t0+i*per, t0+i*per+dur))
        if out_t is not None: a *= 1 - smooth(seg(t, out_t+i*0.015, out_t+i*0.015+out_dur))
        amax = max(amax, a)
        if a > 0.004:
            y = pad + rise*px*(1-a)
            ds.text((x+px*0.05, y+px*0.07), c, font=f, fill=(0, 0, 0, int(190*a))); d.text((x, y), c, font=f, fill=tuple(color)+(int(255*a),))
        x += adv[i]
    if amax <= 0.004: return 0.0
    if shadow: tile = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(px*0.06)), tile)
    if glow:
        g = tile.filter(ImageFilter.GaussianBlur(px*0.12)); g.putalpha(g.getchannel("A").point(lambda v: int(min(255, v*glow)))); tile = Image.alpha_composite(g, tile)
    if abs(angle) > 0.01: tile = tile.rotate(angle, resample=Image.BICUBIC, expand=True)
    cx, cy = view.pt(p_src); ox = {"center": tile.width/2, "left": pad, "right": tile.width-pad}[anchor]
    ui.alpha_composite(tile, (int(cx-ox), int(cy-tile.height/2))) if (0 <= cx-ox and 0 <= cy-tile.height/2 and cx-ox+tile.width <= W and cy-tile.height/2+tile.height <= H) else _paste_clip(ui, tile, int(cx-ox), int(cy-tile.height/2))
    if group is not None: UIREG.append((group, cx-ox+pad, cy-tile.height/2+pad, cx-ox+tile.width-pad, cy+tile.height/2-pad, amax))
    return amax

def _paste_clip(ui, tile, x, y):
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x+tile.width), min(H, y+tile.height)
    if x1 <= x0 or y1 <= y0: return
    ui.alpha_composite(tile.crop((x0-x, y0-y, x1-x, y1-y)), (x0, y0))

def screen_text(ui, xy, text, px, t, t0, color=TEXT, track=0.0, per=0.04, dur=0.4, rise=0.3, out_t=None, out_dur=0.3, shadow=True, group=None, bold=True, glow=None):
    """kinetic text at a fixed screen position (same letter animation as anchored_text)."""
    class _V: k = 1.0
    class _View:
        k = 1.0
        def pt(self, p): return np.array(p, float)
    return anchored_text(ui, _View(), (xy[0], xy[1]), text, px, t, t0, color, track, 0.0, dur, per, rise, out_t, out_dur, px, px, shadow, group, "left", glow)

def year_roll(ui, xy, y_from, y_to, t, t0, dur=0.7, px=120, color=TEXT, stagger=0.09, group=None):
    """rolling digits: digits that differ scroll vertically from the old to the new value."""
    f = tfont(px); cw = f.getlength("0")+px*0.04; hh = int(px*1.25); a, b = str(y_from), str(y_to); x0, y0 = xy
    tile = Image.new("RGBA", (int(cw*len(b))+20, hh+10), (0, 0, 0, 0)); d = ImageDraw.Draw(tile, "RGBA")
    for i, (o, n) in enumerate(zip(a, b)):
        e = smoother(seg(t, t0+i*stagger, t0+i*stagger+dur)) if o != n else 1.0
        cell = Image.new("RGBA", (int(cw)+4, hh), (0, 0, 0, 0)); dc = ImageDraw.Draw(cell, "RGBA")
        if o != n:
            dc.text((2, -e*hh*0.9), o, font=f, fill=tuple(color)+(int(255*(1-e)),)); dc.text((2, (1-e)*hh*0.9), n, font=f, fill=tuple(color)+(int(255*e),))
        else: dc.text((2, 0), n, font=f, fill=tuple(color)+(255,))
        tile.alpha_composite(cell, (int(i*cw)+8, 4))
    sh = tile.copy(); sh = ImageChops.multiply(sh, Image.new("RGBA", sh.size, (0, 0, 0, 160))); sh = sh.filter(ImageFilter.GaussianBlur(px*0.05))
    ui.alpha_composite(sh, (int(x0+px*0.04), int(y0+px*0.06))); ui.alpha_composite(tile, (int(x0), int(y0)))
    if group is not None: UIREG.append((group, x0, y0, x0+tile.width, y0+tile.height, 1.0))

# ---- trails ---------------------------------------------------------------------------------------------------------
def trail(stroke, pts_screen, head_frac, tail_frac=0.28, width=3.2, alpha=1.0, steps=26):
    """polyline revealed up to head_frac with a bright comet head and a fading tail (alpha ramps along the last tail_frac)."""
    p = np.asarray(pts_screen, float)
    if len(p) < 2: return None
    c = cumlen(p); L = c[-1]; h = clamp(head_frac)*L; t0 = max(0.0, h - tail_frac*L)
    # body: everything revealed, dim; tail: bright ramp
    body, _ = partial(p, c, clamp(head_frac)); stroke.line(body, width*0.85, alpha*0.9)
    for i in range(steps):
        a, b = t0 + (h-t0)*i/steps, t0 + (h-t0)*(i+1)/steps
        if b <= a: continue
        seg_pts = _slice(p, c, a, b); stroke.line(seg_pts, width*(0.7+0.9*(i+1)/steps), alpha*(0.35+0.65*(i+1)/steps))
    head = partial(p, c, clamp(head_frac))[1]; return head
def _slice(p, c, a, b):
    ia = int(np.searchsorted(c, a, side="right")-1); ib = int(np.searchsorted(c, b, side="left"))
    ia = max(0, min(ia, len(p)-2)); ib = max(ia+1, min(ib, len(p)-1))
    fa = (a-c[ia])/max(c[ia+1]-c[ia], 1e-9); pa = p[ia] + (p[ia+1]-p[ia])*fa
    ib2 = min(max(int(np.searchsorted(c, b, side="right")-1), 0), len(p)-2); fb = (b-c[ib2])/max(c[ib2+1]-c[ib2], 1e-9); pb = p[ib2] + (p[ib2+1]-p[ib2])*fb
    mid = p[ia+1:ib2+1] if ib2 >= ia+1 else np.empty((0, 2)); return np.vstack([pa, mid, pb])
