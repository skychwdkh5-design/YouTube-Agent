"""MOBILE_READABILITY_QA for the EP004 build (reuses orbitalatlas.mobile_qa checks on review.build's programme).
    python3 productions/ep004-jakarta/build/mqa.py OUT.json [--fps 1] [--start S --end E]"""
import json, os, sys
from collections import defaultdict
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
import review as R
from orbitalatlas import mobile_qa as M, textrec

def tag_kit():
    import ep4kit as X
    from orbitalatlas.layers import Overlay
    for n, c in vars(X).items():
        if isinstance(c, type) and issubclass(c, Overlay) and "draw" in c.__dict__:
            f = c.__dict__["draw"]
            def w(self, ctx, _f=f, _n=n):
                prev = textrec.STATE["tag"]; textrec.STATE["tag"] = _n
                try: return _f(self, ctx)
                finally: textrec.STATE["tag"] = prev
            c.draw = w
    for n in ("OrbitDiagram", "DykeDiagram", "CoherenceDiagram", "TrendsDiagram"):
        c = getattr(X, n); f = c.render
        def w2(self, t, _f=f, _n=n):
            prev = textrec.STATE["tag"]; textrec.STATE["tag"] = _n
            try: return _f(self, t)
            finally: textrec.STATE["tag"] = prev
        c.render = w2


def main():
    tag_kit()
    out = sys.argv[1]; fps = float(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 1.0
    rng = (float(sys.argv[sys.argv.index("--start") + 1]), float(sys.argv[sys.argv.index("--end") + 1])) if "--start" in sys.argv else None
    size = (1280, 720); prog, info = R.build(size, rng); M._wrap_overlays(prog, set()); issues = defaultdict(list); styles = defaultdict(lambda: dict(min_px=1e9, n=0))
    t0 = rng[0] if rng else 0.0; t1 = rng[1] if rng else R.DUR
    for t in np.arange(t0 + 0.5, t1, 1.0 / fps):
        textrec.STATE["rec"] = recs = []
        try: frame = prog.render(float(t) - info["t_base"])
        finally: textrec.STATE["rec"] = None
        M.check_records(recs, frame, size, round(float(t), 2), issues)
        for r in recs: s = styles[r["tag"] or "?"]; s["min_px"] = min(s["min_px"], r["px"] * 1080 / size[1]); s["n"] += 1
    res = dict(rules=dict(min_text_px_1080=M.MIN_TEXT_PX, min_caption_px_1080=M.MIN_CAPTION_PX), styles={k: round(v["min_px"], 1) for k, v in sorted(styles.items())}, issues={})
    for kind, lst in issues.items():
        agg = {}
        for t, r, why in lst:
            key = (r["tag"], r["text"][:40])
            if key not in agg: agg[key] = dict(tag=r["tag"], text=r["text"][:60], first_t=t, last_t=t, count=0, why=why)
            agg[key]["last_t"] = t; agg[key]["count"] += 1
        res["issues"][kind] = sorted(agg.values(), key=lambda x: x["first_t"])
    res["summary"] = {k: len(v) for k, v in res["issues"].items()}; json.dump(res, open(out, "w"), indent=1, ensure_ascii=False); print(json.dumps(dict(summary=res["summary"], styles=res["styles"]), indent=1))
main()
