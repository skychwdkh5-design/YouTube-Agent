"""text QA for the Shorts: every 0.1 s, record all type, check the safe box (x 80-940, y 250-1380; source chips allowed above it),
the 30 px floor (mobile_qa) and simultaneous text load. python3 qa_text.py NAME [step]"""
import os, sys, json
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shorts_build as B
from orbitalatlas import shorts as SH, textrec as TR

SH_ = None


def job(t):
    TR.STATE["rec"] = []; SH_.render(t); recs = TR.STATE["rec"]; TR.STATE["rec"] = None
    big = [r for r in recs if r["px"] >= 48]
    return dict(t=round(t, 2), bad=SH.check_safe(recs), small=[(r["text"], r["px"]) for r in recs if r["px"] < 30], words=sum(len(r["text"].split()) for r in big))


if __name__ == "__main__":
    name = sys.argv[1]; step = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1; SH_ = B.SHORTS[name]()
    ts = [i * step for i in range(int(round(B.DUR / step)))]
    with Pool(4) as p: res = p.map(job, ts)
    bad = [r for r in res if r["bad"] or r["small"]]
    out = dict(name=name, frames=len(res), violations=bad[:40], n_violations=len(bad), max_words_on_screen=max(r["words"] for r in res))
    print(json.dumps(out, indent=1, ensure_ascii=False))
