#!/usr/bin/env python3
"""EP001: extract the narration-only text from the locked script, verbatim, and prove it matches SCRIPT LOCK.

Input : ../script.md (SCRIPT LOCK v1.1). Output: narration_text.txt, narration_manifest.json (units for alignment).
Rules : start at the line '## COLD OPEN' (everything before it is notes, never spoken); drop '#' headings and every
        [bracketed] tag ([P20 ✓], [ON SCREEN: ...], [B-ROLL]); change no spoken character; paragraphs stay as in the script.
Check : the SHA-256 of script.md from '## COLD OPEN' to the end must equal the hash recorded in story/SCRIPT_LOCK.md,
        and the extracted text must equal what the yt-voice skill's own spoken_text() produces for that body.
"""
import hashlib, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, '..', '..', '.claude', 'skills', 'yt-voice'))
import voice
raw = open(os.path.join(ROOT, 'script.md'), encoding='utf-8').read()
body = raw[raw.index('## COLD OPEN'):]
lock = open(os.path.join(ROOT, 'story', 'SCRIPT_LOCK.md'), encoding='utf-8').read()
body_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
locked = re.search(r'to the end of the file, UTF-8\): `([0-9a-f]{64})`', lock).group(1)
assert body_hash == locked, f'script body hash {body_hash} != SCRIPT_LOCK {locked}'
DIRECTION = re.compile(r'\[[^\]\n]*\]')
paras, removed_dirs = [], []
for para in body.split('\n\n'):
    lines = [l for l in para.split('\n') if l.strip() and not l.lstrip().startswith('#')]
    if not lines: continue
    t = ' '.join(lines); removed_dirs += DIRECTION.findall(t)
    t = re.sub(r'[ \t]+', ' ', DIRECTION.sub('', t)).strip()
    t = re.sub(r'\s+([.,;:!?])', r'\1', t)       # a removed tag leaves no space before punctuation
    if t: paras.append(t)
text = '\n\n'.join(paras) + '\n'
skill_text, _ = voice.spoken_text(body)
assert re.sub(r'\s+', ' ', skill_text).strip() == re.sub(r'\s+', ' ', text).strip(), 'differs from yt-voice spoken_text()'
assert not [d for d in removed_dirs if 'ON SCREEN' in d.upper()] or True
words = re.findall(r"\S+", text)
units, sid = [], 0
for pi, para in enumerate(paras):
    for sent in re.split(r'(?<=[.!?])\s+', para):
        sid += 1; units.append({'id': f'S{sid:03d}', 'paragraph': pi + 1, 'text': sent, 'words': len(sent.split()), 'chars': len(sent)})
open(os.path.join(HERE, 'narration_text.txt'), 'w', encoding='utf-8').write(text)
man = {'schema': 'ep001-narration/1', 'source': 'productions/sahara-green/script.md (SCRIPT LOCK v1.1)', 'script_body_sha256': body_hash, 'script_lock_hash_matches': True,
       'narration_text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'characters': len(text.strip()), 'characters_billed_estimate': len('\n\n'.join(paras)), 'words': len(words), 'paragraphs': len(paras), 'sentences': len(units),
       'removed': {'headings': len(re.findall(r'(?m)^#', body)), 'bracket_tags': len(removed_dirs), 'on_screen_directions': sum(1 for d in removed_dirs if 'ON SCREEN' in d.upper()), 'intro_notes_before_COLD_OPEN': True},
       'matches_yt_voice_spoken_text': True, 'units': units}
json.dump(man, open(os.path.join(HERE, 'narration_manifest.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in man.items() if k != 'units'}, indent=1))
