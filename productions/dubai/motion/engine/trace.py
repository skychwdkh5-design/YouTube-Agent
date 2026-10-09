"""Land/sea contour tracing for one source image, numpy + Pillow only.
Outlines are computed from the pixels of the image they are drawn on, so they are registered to that image
by construction. They are NOT survey boundaries and carry no geographic coordinates.
Pipeline: half-resolution box average -> dark threshold -> sea = dark region connected to seed pixels
(run-length union-find) -> marching squares on the sea mask -> smoothing -> Douglas-Peucker -> JSON in
FULL-RESOLUTION edge coordinates (x right, y down, same convention as PIL crop boxes)."""
import json, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def half(img):
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    h, w = a.shape[0]//2*2, a.shape[1]//2*2
    a = a[:h, :w]
    return a.reshape(h//2, 2, w//2, 2, 3).mean(axis=(1, 3))

def sea_mask(gray_dark, seeds):
    """4-connected components of gray_dark via run-length union-find; keep components containing seed pixels."""
    H, W = gray_dark.shape
    parent = []
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    runs = []      # per row list of (start, end, id)
    prev = []
    for r in range(H):
        d = gray_dark[r].astype(np.int8)
        dd = np.diff(np.concatenate(([0], d, [0])))
        st = np.where(dd == 1)[0]; en = np.where(dd == -1)[0]
        cur = []
        for s, e in zip(st, en):
            i = len(parent); parent.append(i); cur.append((s, e, i))
        a = b = 0
        while a < len(prev) and b < len(cur):
            ps, pe, pi = prev[a]; cs, ce, ci = cur[b]
            if ps < ce and cs < pe:
                ra, rb = find(pi), find(ci)
                if ra != rb: parent[ra] = rb
            if pe < ce: a += 1
            else: b += 1
        runs.append(cur); prev = cur
    seed_ids = set()
    for r in range(H):
        for s, e, i in runs[r]:
            if seeds[r] and s <= seeds_col(seeds, r) < e: seed_ids.add(find(i))
    out = np.zeros((H, W), bool)
    for r in range(H):
        for s, e, i in runs[r]:
            if find(i) in seed_ids: out[r, s:e] = True
    return out
def seeds_col(seeds, r): return 0

_SEG = {1: [("l", "b")], 2: [("b", "r")], 3: [("l", "r")], 4: [("t", "r")], 5: [("t", "l"), ("b", "r")], 6: [("t", "b")],
        7: [("t", "l")], 8: [("t", "l")], 9: [("t", "b")], 10: [("t", "r"), ("l", "b")], 11: [("t", "r")], 12: [("l", "r")],
        13: [("b", "r")], 14: [("l", "b")]}
def marching(M):
    P = np.pad(M, 1, mode="edge").astype(np.uint8)
    case = P[:-1, :-1]*8 + P[:-1, 1:]*4 + P[1:, 1:]*2 + P[1:, :-1]
    ii, jj = np.where((case > 0) & (case < 15))
    mid = lambda i, j, k: {"t": (2*i, 2*j+1), "b": (2*i+2, 2*j+1), "l": (2*i+1, 2*j), "r": (2*i+1, 2*j+2)}[k]
    adj = {}
    for i, j in zip(ii.tolist(), jj.tolist()):
        for a, b in _SEG[int(case[i, j])]:
            pa, pb = mid(i, j, a), mid(i, j, b)
            adj.setdefault(pa, []).append(pb); adj.setdefault(pb, []).append(pa)
    seen, polys = set(), []
    def walk(start):
        path = [start]; seen.add(start); cur = start; prev = None
        while True:
            nxt = [n for n in adj[cur] if n != prev and n not in seen]
            if not nxt:
                if len(path) > 2 and start in adj[cur] and cur != start and prev is not None and start in adj[cur]:
                    path.append(start)
                break
            prev, cur = cur, nxt[0]; seen.add(cur); path.append(cur)
        return path
    for p in [p for p, n in adj.items() if len(n) == 1]:
        if p not in seen: polys.append(walk(p))
    for p in list(adj):
        if p not in seen: polys.append(walk(p))
    # padded doubled coordinates -> mask index coordinates (pixel-centre indices)
    return [np.array([[(c[1]-2)/2.0, (c[0]-2)/2.0] for c in p]) for p in polys]

def smooth(p, n=2):
    for _ in range(n):
        if len(p) < 5: break
        closed = np.allclose(p[0], p[-1])
        q = p.copy()
        q[1:-1] = (p[:-2] + 2*p[1:-1] + p[2:]) / 4
        if closed: q[0] = q[-1] = (p[-2] + 2*p[0] + p[1]) / 4
        p = q
    return p

def dp(p, tol):
    if len(p) < 3: return p
    keep = np.zeros(len(p), bool); keep[0] = keep[-1] = True
    stack = [(0, len(p)-1)]
    while stack:
        s, e = stack.pop()
        a, b = p[s], p[e]; ab = b - a; L = np.hypot(*ab)
        seg = p[s+1:e]
        if len(seg) == 0: continue
        d = np.hypot(*(seg-a).T) if L == 0 else np.abs(ab[0]*(seg[:, 1]-a[1]) - ab[1]*(seg[:, 0]-a[0])) / L
        k = int(np.argmax(d))
        if d[k] > tol: keep[s+1+k] = True; stack += [(s, s+1+k), (s+1+k, e)]
    return p[keep]

def length(p): return float(np.hypot(*np.diff(p, axis=0).T).sum()) if len(p) > 1 else 0.0

def trace(path, thresh=70.0, min_len=6.0, tol=0.6):
    im = Image.open(path)
    h = half(im); gmax = h.max(axis=2)
    # sea statistics from a left strip away from the top-left cloud corner
    H, W = gmax.shape
    strip = gmax[int(H*0.25):int(H*0.7), 0:int(W*0.08)]
    sea_hi = float(np.percentile(strip, 99.5))
    # sea_hi is deep-sea noise (about 17); shallows and lagoon water reach about 45, land edges exceed about 170.
    # thresh=70 (max-channel, half-res) separates all water from land; found by sampling the profile across the Jebel Ali ring.
    T = thresh if thresh is not None else sea_hi + 10
    dark = gmax < T
    seeds = np.zeros(H, bool); seeds[int(H*0.12):int(H*0.9)] = dark[int(H*0.12):int(H*0.9), 0]
    sea = sea_mask(dark, seeds)
    polys = marching(sea)
    out = []
    for p in polys:
        if length(p) < min_len: continue
        p = dp(smooth(p), tol)
        out.append((p*2 + 1).round(1))      # half-res index -> full-res edge coords
    return out, dict(T=T, sea_hi=sea_hi, half_size=(W, H), n_raw=len(polys), n_kept=len(out))

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    polys, info = trace(src)
    json.dump({"source": src.split("/")[-1], "info": info, "coords": "full-resolution edge coordinates, x right, y down",
               "polylines": [p.tolist() for p in polys]}, open(dst, "w"), separators=(",", ":"))
    print(info, "points", sum(len(p) for p in polys))
