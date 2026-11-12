"""Mesh skinning and a small triangle rasteriser (numpy only).

Each part image gets a grid mesh. Every vertex carries bone weights (linear blend
skinning): inside a joint zone it blends between its own bone and the neighbour, so cloth
bends smoothly across a joint instead of two rigid pictures rotating against each other.
Rigid parts use one quad (weights 1 to a single bone).
"""
import math
import numpy as np
from PIL import Image

from .mathx import ap_many, smoothstep


class SkinnedPart:
    def __init__(self, part, J):
        self.name = part.name
        self.bone = part.bone
        img = part.img
        self.levels = [_premult(img)]
        h, w = img.shape[:2]
        im2 = Image.fromarray((img * 255).astype(np.uint8), 'RGBA').resize((max(1, w // 2), max(1, h // 2)), Image.BOX)
        self.levels.append(_premult(np.asarray(im2).astype(np.float32) / 255))
        nx, ny = part.grid
        xs = np.linspace(0, w, nx + 1)
        ys = np.linspace(0, h, ny + 1)
        gx, gy = np.meshgrid(xs, ys)
        self.U = np.stack([gx.ravel(), gy.ravel()], 1)                 # image px
        self.Vrest = ap_many(part.M, self.U)                            # rest frame
        # active cells (skip fully transparent ones)
        al = img[..., 3]
        tris = []
        for j in range(ny):
            for i in range(nx):
                x0, x1 = int(xs[i]), int(math.ceil(xs[i + 1]))
                y0, y1 = int(ys[j]), int(math.ceil(ys[j + 1]))
                if al[max(0, y0 - 1):y1 + 1, max(0, x0 - 1):x1 + 1].max() <= 0.004:
                    continue
                a = j * (nx + 1) + i
                b, c, d = a + 1, a + nx + 1, a + nx + 2
                tris += [(a, b, d), (a, d, c)]
        self.tris = np.array(tris, int).reshape(-1, 3)
        # skin weights: {bone: weight array}
        n = len(self.Vrest)
        own = np.ones(n)
        self.weights = {}
        for z in part.zones:
            jp = J[z.joint]
            d = (self.Vrest - jp) @ z.axis                       # distance into this part
            u_in = np.clip(d / z.zone, 0, 1)
            u_out = np.clip(-d / z.zone, 0, 1)
            s_in = u_in * u_in * (3 - 2 * u_in)
            s_out = u_out * u_out * (3 - 2 * u_out)
            w = np.where(d >= 0, z.cap * (1 - s_in), z.cap + (1 - z.cap) * s_out)
            # only near the joint across the bone, not along the whole image edge
            w = np.minimum(w, own)
            self.weights[z.other] = self.weights.get(z.other, 0) + w
            own = own - w
        self.weights[part.bone] = own

    def deform(self, bone_world, screen):
        """bone_world: {bone: 3x3 rest->world}. Returns screen-space vertices."""
        V = np.zeros_like(self.Vrest)
        for b, w in self.weights.items():
            if np.ndim(w) == 0 and w == 0:
                continue
            V += (ap_many(bone_world[b], self.Vrest)) * np.asarray(w)[:, None]
        return ap_many(screen, V)

    def draw(self, canvas, Vs):
        if not len(self.tris):
            return
        # pick a mip level from the on-screen scale
        e = self.tris[0]
        su = np.linalg.norm(self.U[e[1]] - self.U[e[0]]) + 1e-9
        sv = np.linalg.norm(Vs[e[1]] - Vs[e[0]])
        lvl = 1 if sv / su < 0.6 else 0
        rasterize(canvas, self.levels[lvl], self.U / (2 ** lvl), Vs, self.tris)


def _premult(img):
    out = img.copy()
    out[..., :3] *= out[..., 3:4]
    return out


def rasterize(canvas, src, U, V, tris, eps=1e-6):
    """Map the source mesh (U, source px) onto V (canvas px), compositing premultiplied
    RGBA 'over' the canvas. Each pixel is owned by exactly one triangle (no seams, no
    double coverage along shared edges)."""
    H, W = canvas.shape[:2]
    P = V[tris]                                       # (n,3,2)
    x0 = max(0, int(math.floor(P[..., 0].min())))
    y0 = max(0, int(math.floor(P[..., 1].min())))
    x1 = min(W, int(math.ceil(P[..., 0].max())) + 1)
    y1 = min(H, int(math.ceil(P[..., 1].max())) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    bw, bh = x1 - x0, y1 - y0
    sx = np.full((bh, bw), -1.0, np.float32)
    sy = np.full((bh, bw), -1.0, np.float32)
    own = np.zeros((bh, bw), bool)
    for k, (ia, ib, ic) in enumerate(tris):
        a, b, c = V[ia], V[ib], V[ic]
        tx0 = max(x0, int(math.floor(min(a[0], b[0], c[0]))))
        ty0 = max(y0, int(math.floor(min(a[1], b[1], c[1]))))
        tx1 = min(x1, int(math.ceil(max(a[0], b[0], c[0]))) + 1)
        ty1 = min(y1, int(math.ceil(max(a[1], b[1], c[1]))) + 1)
        if tx1 <= tx0 or ty1 <= ty0:
            continue
        m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
        det = m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0]
        if abs(det) < 1e-9:
            continue
        inv = np.array([[m[1, 1], -m[0, 1]], [-m[1, 0], m[0, 0]]]) / det
        px = np.arange(tx0, tx1) + 0.5 - a[0]
        py = np.arange(ty0, ty1) + 0.5 - a[1]
        PX, PY = np.meshgrid(px, py)
        l1 = inv[0, 0] * PX + inv[0, 1] * PY
        l2 = inv[1, 0] * PX + inv[1, 1] * PY
        l0 = 1 - l1 - l2
        sub = own[ty0 - y0:ty1 - y0, tx0 - x0:tx1 - x0]
        ins = (l0 >= -eps) & (l1 >= -eps) & (l2 >= -eps) & ~sub
        if not ins.any():
            continue
        ua, ub, uc = U[ia], U[ib], U[ic]
        sxs = sx[ty0 - y0:ty1 - y0, tx0 - x0:tx1 - x0]
        sys_ = sy[ty0 - y0:ty1 - y0, tx0 - x0:tx1 - x0]
        sxs[ins] = (l0 * ua[0] + l1 * ub[0] + l2 * uc[0])[ins]
        sys_[ins] = (l0 * ua[1] + l1 * ub[1] + l2 * uc[1])[ins]
        sub[ins] = True
    if not own.any():
        return
    col = sample(src, sx, sy) * own[..., None]
    dst = canvas[y0:y1, x0:x1]
    dst *= (1 - col[..., 3:4])
    dst += col


def sample(src, x, y):
    """Bilinear sample of premultiplied src at pixel-centre coords; zero outside."""
    h, w = src.shape[:2]
    fx = x - 0.5
    fy = y - 0.5
    x0 = np.floor(fx).astype(int)
    y0 = np.floor(fy).astype(int)
    ax = (fx - x0)[..., None]
    ay = (fy - y0)[..., None]
    pad = np.zeros((h + 2, w + 2, 4), np.float32)
    pad[1:-1, 1:-1] = src
    xi = np.clip(x0 + 1, 0, w + 1)
    yi = np.clip(y0 + 1, 0, h + 1)
    xj = np.clip(x0 + 2, 0, w + 1)
    yj = np.clip(y0 + 2, 0, h + 1)
    out = (pad[yi, xi] * (1 - ax) * (1 - ay) + pad[yi, xj] * ax * (1 - ay)
           + pad[yj, xi] * (1 - ax) * ay + pad[yj, xj] * ax * ay)
    return out


def quad_mesh(w, h):
    U = np.array([[0, 0], [w, 0], [0, h], [w, h]], float)
    tris = np.array([[0, 1, 3], [0, 3, 2]])
    return U, tris
