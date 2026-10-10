"""EP002 on-screen label audit: every year shown on screen must come from (a) the asset actually displayed in that scene (file date table in scenes.YEAR/DATE)
or (b) the locked narration of that scene (script_draft_v1_2.md VO lines). Anything else is reported. Also lists every distinct on-screen string per scene
so a person can read the full label inventory. Usage: python3 audit_labels.py [OUT.json] [OUT.md]   (EP002_WOC points at the extracted WoC frames)"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit, scenes as S
from build_preview import vo_lines
vo = vo_lines(); kit.LOG = True; Y = re.compile(r'\b(19|20)\d{2}\b'); rows = []; flagged = []
for sid, start, dur, vos, fn in S.SCENES:
    kit.REC = []; kit.USED.clear(); keys = set()
    for k in range(int(dur / 0.5) + 1):
        try: fn(min(k * 0.5, dur - 1e-3), dur, {'a1_frames': []})
        except Exception:
            if sid != 'A1': raise
    keys = {key for key, _ in kit.USED}; strings = sorted(set(kit.REC))
    allowed = {S.YEAR[k] for k in keys if k in S.YEAR} | ({'2022'} if 'iss' in keys else set()) | set(m.group(0) for l in [vo[i - 1] for i in vos] for m in Y.finditer(l))
    allowed |= getattr(S, 'EXTRA_YEARS', {}).get(sid, (set(), ''))[0]
    if sid == 'A1': allowed |= {'2000'}                                   # the A2 start crop appears in the dissolve
    bad = [(s, y.group(0)) for s in strings for y in Y.finditer(s) if y.group(0) not in allowed]
    rows.append(dict(scene=sid, assets=sorted(keys), strings=strings, flagged=bad)); flagged += [(sid,) + b for b in bad]
kit.REC = None
out = dict(verdict='PASS' if not flagged else 'FAIL', flagged=flagged, scenes=rows)
if len(sys.argv) > 1: json.dump(out, open(sys.argv[1], 'w'), indent=1)
if len(sys.argv) > 2:
    L = ['| scene | assets shown | on-screen strings (distinct) | flagged years |', '|---|---|---|---|'] + [f"| {r['scene']} | {', '.join(r['assets']) or 'none'} | {'; '.join(r['strings'])} | {r['flagged'] or 'none'} |" for r in rows]
    open(sys.argv[2], 'w').write('\n'.join(L) + '\n')
print(out['verdict'], flagged)
