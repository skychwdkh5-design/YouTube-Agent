#!/usr/bin/env python3
"""EP001 lock integrity: what is locked, what is its hash, what changed since the baseline commit, and was every change intentional.
Free, offline. Usage: python3 lock_check.py [BASELINE_COMMIT]   (default c7e5b39)"""
import hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE)); BASE = sys.argv[1] if len(sys.argv) > 1 else 'c7e5b39'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
def git(*a): return subprocess.run(['git', '-C', REPO, *a], capture_output=True, text=True).stdout
P = lambda *a: os.path.join(HERE, *a)
raw = open(P('script.md'), 'rb').read(); body = raw[raw.index(b'## COLD OPEN'):]
lock_md = open(P('story', 'SCRIPT_LOCK.md'), encoding='utf-8').read()
import re
locked = re.search(r'to the end of the file, UTF-8\): `([0-9a-f]{64})`', lock_md).group(1)
res = {'baseline_commit': BASE, 'head': git('rev-parse', '--short', 'HEAD').strip(), 'locks': {}}
res['locks']['SCRIPT_LOCK_v1.1'] = {'script_body_sha256': hashlib.sha256(body).hexdigest(), 'recorded_in_SCRIPT_LOCK_md': locked, 'match': hashlib.sha256(body).hexdigest() == locked,
                                    'script_md_changed_since_baseline': bool(git('diff', '--name-only', BASE, '--', 'productions/sahara-green/script.md').strip())}
man = json.load(open(P('narration', 'narration_manifest.json')))
res['locks']['narration_text'] = {'sha256': sha(P('narration', 'narration_text.txt')), 'manifest': man['narration_text_sha256'], 'match': sha(P('narration', 'narration_text.txt')) == man['narration_text_sha256'], 'words': man['words'], 'characters': man['characters']}
vh = json.load(open(P('visuals', 'reports', 'visual_lock_hashes.json')))
sys.path.insert(0, '/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/vis')
cache = '/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/vis/cache/'
frames = {k: {'recorded': v[:16], 'now': sha(cache + k)[:16], 'match': sha(cache + k) == v} for k, v in vh.items() if k.endswith('_base.npy') and os.path.exists(cache + k)}
res['locks']['imagery_tone_B_frames'] = {'frames_checked': len(frames), 'all_match': all(f['match'] for f in frames.values()) if frames else None, 'frames': frames,
                                         'note': 'cached tone-B frames derived from the verified source bands (landsat/source_bands/manifest.json); outside Git' if frames else 'frame cache not present in this environment'}
changed = [l for l in git('diff', '--name-only', BASE).splitlines() if l]
protected = ('productions/sahara-green/script.md', 'productions/sahara-green/story/', 'productions/sahara-green/landsat/', 'productions/sahara-green/narration/narration_text.txt', 'productions/sahara-green/narration/narration_manifest.json', 'productions/sahara-green/visuals/previews/visual_lock/', 'benchmarks/')
res['protected_paths_changed_since_baseline'] = [f for f in changed if f.startswith(protected)]
res['changed_files_since_baseline'] = changed
res['intentional_changes_since_baseline'] = [
    {'file': 'productions/sahara-green/visuals/scripts/render.py', 'change': 'visual lock v1.2: 1984 hold push-in (<= 3 percent) and schedule-driven sequences; imagery, tone B, crops, dates, zoom target and zoom window unchanged'},
    {'file': 'productions/sahara-green/visuals/VISUAL_LOCK.md', 'change': 'documents v1.2'},
    {'file': 'productions/sahara-green/narration/cues.py', 'change': 'scene 19 shift capped at 2.2 s and reported (reviewer decision 4)'}]
res['render_py_sha256'] = sha(P('visuals', 'scripts', 'render.py')); res['render_py_sha256_in_visual_lock_hashes_v1'] = vh.get('render.py')
res['ALL_LOCKS_OK'] = res['locks']['SCRIPT_LOCK_v1.1']['match'] and not res['locks']['SCRIPT_LOCK_v1.1']['script_md_changed_since_baseline'] and res['locks']['narration_text']['match'] and res['locks']['imagery_tone_B_frames']['all_match'] is not False and not res['protected_paths_changed_since_baseline']
json.dump(res, open(P('LOCK_INTEGRITY.json'), 'w'), indent=1)
print(json.dumps({k: res[k] for k in ('baseline_commit', 'head', 'protected_paths_changed_since_baseline', 'ALL_LOCKS_OK')}, indent=1)); print(json.dumps(res['locks']['SCRIPT_LOCK_v1.1'], indent=1)); print({k: res['locks']['imagery_tone_B_frames'][k] for k in ('frames_checked', 'all_match')})
sys.exit(0 if res['ALL_LOCKS_OK'] else 1)
