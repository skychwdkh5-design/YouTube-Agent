"""Sequential frame readers for the owner's silent NASA clips, plus framing (fill / square / pillar / track).
A source frame is always a real decoded frame (nearest, held) - no interpolation, no invented in-betweens."""
import os, subprocess
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from paint import W, H

SRC_DIR = os.environ.get("BENNU_SRC", "")
SOURCES = {  # id: (file, width, height, fps)
    "M01": ("M01_samcam_silent.mp4", 1024, 1024, 30.0),
    "M02": ("M02_silent.mp4", 1024, 1024, 30.0),
    "M03": ("M03_silent.mp4", 1920, 1080, 60000 / 1001),
    "M04": ("M04_silent.mp4", 1920, 1080, 30000 / 1001),
    "M05": ("M05_silent.mp4", 1920, 1080, 30.0),
    "M06": ("M06_silent.mp4", 1920, 1080, 60000 / 1001),
    "M08": ("M08_silent.mp4", 1920, 1080, 10.0),
    "M09": ("M09_silent.mp4", 1920, 1080, 30.0),
    "M10": ("M10_silent.mp4", 1920, 1080, 30.0),
    "M11": ("M11_silent.mp4", 1280, 720, 30000 / 1001),
}


class Reader:
    def __init__(self, sid):
        self.sid = sid
        self.f, self.w, self.h, self.fps = SOURCES[sid]
        self.p = None
        self.idx = None   # absolute index of self.cur
        self.cur = None

    def _open(self, idx):
        if self.p:
            self.p.kill(); self.p.wait()
        t = max(0.0, idx / self.fps - 0.001)
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", os.path.join(SRC_DIR, self.f),
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 8)
        self.idx = idx - 1
        self.cur = None
        self._read()

    def _read(self):
        n = self.w * self.h * 3
        b = self.p.stdout.read(n)
        if len(b) < n:  # end of file: hold the last frame
            return False
        self.cur = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
        self.idx += 1
        return True

    def get(self, ts):
        idx = max(0, int(ts * self.fps + 1e-6))
        if self.p is None or idx < self.idx or idx > self.idx + 90:
            self._open(idx)
        while self.idx < idx:
            if not self._read():
                break
        return self.cur

    def close(self):
        if self.p:
            self.p.kill(); self.p.wait(); self.p = None


def _bg_fill(img, dark=0.42):
    """blurred, darkened full-frame fill made from the same picture (for square / pillarboxed sources)."""
    s = img.resize((96, 54), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    s = s.resize((W, H), Image.BILINEAR)
    return ImageEnhance.Brightness(s).enhance(dark)


def frame_fill(arr, cx=None, cy=None, zoom=1.0, region=None):
    """cover 1920x1080 from `region` (x0,y0,x1,y1) of the source, zoomed about (cx, cy) in source px."""
    h, w = arr.shape[:2]
    x0, y0, x1, y1 = region or (0, 0, w, h)
    rw, rh = x1 - x0, y1 - y0
    bw = min(rw, rh * 16 / 9) / zoom
    bh = bw * 9 / 16
    cx = (x0 + x1) / 2 if cx is None else cx
    cy = (y0 + y1) / 2 if cy is None else cy
    l = min(max(cx - bw / 2, x0), x1 - bw)
    t = min(max(cy - bh / 2, y0), y1 - bh)
    im = Image.fromarray(arr)
    return im.transform((W, H), Image.EXTENT, (l, t, l + bw, t + bh), Image.BILINEAR)


def frame_fit(arr, region=None, cx_out=W / 2, zoom=1.0, fcx=None, fcy=None, dark=0.42):
    """whole `region` fitted to the frame height (no crop), centred at cx_out, blurred fill outside.
    zoom>1 crops toward (fcx, fcy) inside the region while keeping the same box on screen."""
    h, w = arr.shape[:2]
    x0, y0, x1, y1 = region or (0, 0, w, h)
    im = Image.fromarray(arr)
    sub = im.crop((x0, y0, x1, y1))
    bg = _bg_fill(sub, dark)
    rw, rh = x1 - x0, y1 - y0
    if zoom > 1.0001:
        bw, bh = rw / zoom, rh / zoom
        fcx = rw / 2 if fcx is None else fcx - x0
        fcy = rh / 2 if fcy is None else fcy - y0
        l = min(max(fcx - bw / 2, 0), rw - bw); t = min(max(fcy - bh / 2, 0), rh - bh)
        sub = sub.transform((rw, rh), Image.EXTENT, (l, t, l + bw, t + bh), Image.BILINEAR)
    sc = H / rh
    ow, oh = int(round(rw * sc)), H
    pic = sub.resize((ow, oh), Image.BILINEAR)
    # soft left/right edges into the fill
    mask = Image.new("L", (ow, oh), 255)
    m = np.asarray(mask).astype(np.float32)
    ramp = np.clip(np.minimum(np.arange(ow), ow - 1 - np.arange(ow)) / 28.0, 0, 1)
    m = (m * ramp[None, :]).astype(np.uint8)
    bg.paste(pic, (int(round(cx_out - ow / 2)), 0), Image.fromarray(m, "L"))
    return bg
