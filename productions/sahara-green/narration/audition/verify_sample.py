#!/usr/bin/env python3
"""Proves the audition sample is byte-identical to the locked narration. Free, offline, sends nothing."""
import hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); NAR = os.path.dirname(HERE); ROOT = os.path.dirname(NAR); REPO = os.path.dirname(os.path.dirname(ROOT))
sample = open(os.path.join(HERE, 'sample_text.txt'), 'rb').read()
narr = open(os.path.join(NAR, 'narration_text.txt'), 'rb').read()
man = json.load(open(os.path.join(NAR, 'narration_manifest.json'))); units = {u['id']: u['text'] for u in man['units']}
groups = [['S001', 'S002', 'S003'], ['S047', 'S048', 'S049'], ['S055', 'S056', 'S057', 'S058']]
res = {}
res['narration_text_sha256'] = hashlib.sha256(narr).hexdigest(); res['narration_text_sha256_matches_manifest'] = res['narration_text_sha256'] == man['narration_text_sha256']
raw = open(os.path.join(ROOT, 'script.md'), 'rb').read(); body = raw[raw.index(b'## COLD OPEN'):]
res['script_body_sha256'] = hashlib.sha256(body).hexdigest(); res['script_body_sha256_matches_manifest'] = res['script_body_sha256'] == man['script_body_sha256']
paras = sample.decode('utf-8').rstrip('\n').split('\n\n')
res['sample_paragraphs'] = len(paras)
res['each_paragraph_is_the_concatenation_of_locked_sentences'] = paras == [' '.join(units[i] for i in g) for g in groups]
res['each_paragraph_is_a_byte_exact_substring_of_the_locked_narration_text'] = all(p.encode('utf-8') in narr for p in paras)
res['sample_has_no_markup'] = not any(ch in sample.decode('utf-8') for ch in '[]#')
res['sample_sha256'] = hashlib.sha256(sample).hexdigest(); res['sample_characters'] = len(sample.decode('utf-8').strip())
# what voice.py would send (plan only: no --confirm, nothing leaves this machine)
p = subprocess.run([sys.executable, os.path.join(REPO, '.claude', 'skills', 'yt-voice', 'voice.py'), '--script', os.path.join(HERE, 'sample_text.txt'), '--output', '/tmp/verify_sample.wav', '--max-chars', '700'], capture_output=True, text=True)
plan = json.loads(p.stdout)
res['voice_py_plan_status'] = plan['status']; res['voice_py_billed_characters'] = plan['characters']; res['voice_py_chunks'] = plan['chunks']
res['voice_py_spoken_text_equals_sample_file'] = plan['spoken_text'].strip() == sample.decode('utf-8').strip(); res['voice_py_removed_nothing'] = plan['removed_from_script'] == []
res['ALL_OK'] = all(v for k, v in res.items() if isinstance(v, bool))
json.dump(res, open(os.path.join(HERE, 'sample_verification.json'), 'w'), indent=1)
print(json.dumps(res, indent=1)); sys.exit(0 if res['ALL_OK'] else 1)
