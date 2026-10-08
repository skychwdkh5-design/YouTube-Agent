#!/usr/bin/env python3
"""Restore the EP001 Landsat source bands listed in manifest.json (outside Git).

  python3 restore_source_bands.py --manifest manifest.json --workspace DIR [--check-only] [--budget-bytes N]

Needs env USGS_M2M_USERNAME and USGS_M2M_TOKEN for downloads (never printed or stored).
Verifies size and SHA-512 of every file; downloads only missing or corrupt ones; stops before
exceeding --budget-bytes; a failed file (e.g. HTTP 504) is skipped and reported, run again to resume.
Uses the repo skill .claude/skills/yt-satellite/usgs_m2m.py.
"""
import argparse, hashlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '../../../../../.claude/skills/yt-satellite')))

def sha512(p):
    h = hashlib.sha512()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--manifest', required=True); ap.add_argument('--workspace', required=True)
    ap.add_argument('--check-only', action='store_true'); ap.add_argument('--budget-bytes', type=int, default=2_000_000_000)
    a = ap.parse_args(); man = json.load(open(a.manifest)); missing = []; good = 0
    for s in man['scenes']:
        for f in s['files']:
            p = os.path.join(a.workspace, f['local_path_hint'])
            if os.path.exists(p) and os.path.getsize(p) == f['bytes'] and sha512(p) == f['sha512']: good += 1
            else: missing.append((s, f, p))
    need = sum(f['bytes'] for _, f, _ in missing)
    print(json.dumps({'ok_files': good, 'missing_or_corrupt': len(missing), 'bytes_to_download': need}))
    if a.check_only or not missing: return 0
    if need > a.budget_bytes: print('over budget, stop'); return 2
    import usgs_m2m as u
    with u.M2M() as m:
        for sid in dict.fromkeys(s['displayId'] for s, _, _ in missing):
            items = [(f, p) for s, f, p in missing if s['displayId'] == sid]; label = 'yt-restore-%d' % int(time.time())
            try:
                req = m.call('download-request', {'label': label, 'downloads': [{'entityId': f['sourceEntityId'], 'productId': f['sourceProductId']} for f, _ in items]}) or {}
                avail = list(req.get('availableDownloads') or []); end = time.time() + 180
                while len([d for d in avail if d.get('url')]) < len(items) and time.time() < end:
                    time.sleep(8); avail = list((m.call('download-retrieve', {'label': label}) or {}).get('available') or [])
                by = {d['entityId']: d for d in avail if d.get('url')}
                for f, p in items:
                    d = by.get(f['sourceEntityId'])
                    if not d: print('no URL for', f['name']); continue
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    try: r = m._fetch(d['url'], os.path.dirname(p), f['sourceEntityId'], 100)
                    except u.M2MError as e: print('FAILED', f['name'], str(e)[:80]); continue
                    os.replace(r['path'], p)
                    print(f['name'], 'ok' if sha512(p) == f['sha512'] else 'CHECKSUM MISMATCH')
            finally:
                m.cleanup_order(label)
    return 0
if __name__ == '__main__': sys.exit(main())
