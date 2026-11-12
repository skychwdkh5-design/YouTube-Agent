import numpy as np
from PIL import Image, ImageDraw, ImageFilter
def pushpull(img, known):
    """img HxWx3 float, known HxW bool -> filled smooth image"""
    levels=[]; c=img*known[...,None]; w=known.astype(np.float32)
    while min(w.shape)>4:
        levels.append((c,w))
        h,ww=w.shape; h2,w2=h//2*2,ww//2*2
        c=c[:h2,:w2].reshape(h2//2,2,w2//2,2,3).sum((1,3)); w=w[:h2,:w2].reshape(h2//2,2,w2//2,2).sum((1,3))
    est=c/np.maximum(w,1e-6)[...,None]
    gm=(img*known[...,None]).reshape(-1,3).sum(0)/max(known.sum(),1)
    est=np.where((w>0)[...,None],est,gm)
    for c,w in reversed(levels):
        up=np.asarray(Image.fromarray(np.clip(est,0,255).astype(np.uint8)).resize((w.shape[1],w.shape[0]),Image.BILINEAR)).astype(np.float32)
        a=np.clip(w,0,1)[...,None]
        est=c/np.maximum(w,1e-6)[...,None]*a+up*(1-a)
    return est
def blur(a,r):
    return np.asarray(Image.fromarray(np.clip(a,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)
def texture(shape, tile, seed=1):
    rng=np.random.default_rng(seed); H,W=shape; th,tw=tile.shape[:2]
    hp=tile-blur(tile,6)
    out=np.zeros((H,W,3),np.float32)
    for y in range(0,H,th//2):
        for x in range(0,W,tw//2):
            t=np.roll(hp[::(1 if rng.random()<.5 else -1), ::(1 if rng.random()<.5 else -1)],(int(rng.integers(th)),int(rng.integers(tw))),(0,1))
            hh=min(th,H-y); w2=min(tw,W-x)
            out[y:y+hh,x:x+w2]=t[:hh,:w2]
    return out
def fill(img, hole, tile, feather=6, seed=1):
    """img uint8 RGB array, hole bool mask -> filled uint8"""
    a=img.astype(np.float32)
    known=~hole
    low=pushpull(blur(a,0)*1, known)
    low=blur(low,3)
    tex=texture(hole.shape, tile, seed)
    f=low+tex
    m=np.asarray(Image.fromarray((hole*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(feather))).astype(np.float32)/255
    m=np.maximum(m, hole*1.0)[...,None]
    return np.clip(a*(1-m)+f*m,0,255).astype(np.uint8)
