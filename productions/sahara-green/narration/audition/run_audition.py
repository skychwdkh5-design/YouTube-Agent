#!/usr/bin/env python3
"""EP001 voice audition: the three exact yt-voice commands, Brian, Bill, Adam, one identical 677-character sample.

  python3 run_audition.py                  # FREE: prints the three commands and the plan check (voice.py without --confirm); nothing is sent
  python3 run_audition.py --execute        # PAID: refused unless EP001_AUDITION_AUTHORIZED=2031 is set in the environment

The environment guard is deliberate: the reviewer must have confirmed the credit balance and authorised up to 2,031 credits.
The full narration is NOT part of this script and must not be generated before the reviewer has chosen the voice.
"""
import json, os, shlex, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); NAR = os.path.dirname(HERE); ROOT = os.path.dirname(NAR); REPO = os.path.dirname(os.path.dirname(ROOT))
VOICE_PY = os.path.join(REPO, '.claude', 'skills', 'yt-voice', 'voice.py')
OUT = os.path.join(NAR, 'voice', 'audition')
SETTINGS = '{"stability":0.55,"similarity_boost":0.75,"style":0,"speed":1.0,"use_speaker_boost":true}'
VOICES = [('Brian', 'nPczCjzI2devNBz1zQrb'), ('Bill', 'pqHfZKP75CvOlQylNhV4'), ('Adam', 'pNInz6obpgDQGcFmaJgB')]
CHARS, BUDGET = 677, 2031
def command(name, vid, confirm):
    c = ['python3', VOICE_PY, '--script', os.path.join(HERE, 'sample_text.txt'), '--voice-id', vid, '--output', os.path.join(OUT, f'sample_{name}.wav'),
         '--model', 'eleven_multilingual_v2', '--voice-settings', SETTINGS, '--max-chars', '700', '--auth', 'proxy']
    return c + (['--confirm'] if confirm else [])
def main():
    execute = '--execute' in sys.argv
    for n, v in VOICES:
        print(f'# {n} ({v}), {CHARS} credits\n' + ' '.join(shlex.quote(x) for x in command(n, v, True)) + '\n')
    for n, v in VOICES:
        p = subprocess.run(command(n, v, False), capture_output=True, text=True); d = json.loads(p.stdout)
        assert d['status'] == 'confirm_required' and d['characters'] == CHARS and d['chunks'] == 1 and d['voice_id'] == v and d['model_id'] == 'eleven_multilingual_v2', d
        print(f'plan ok: {n}: {d["characters"]} characters, 1 request, model {d["model_id"]}, nothing sent')
    print(f'total if run: {CHARS * len(VOICES)} credits (multilingual_v2 at 1 credit per character)')
    if not execute:
        return 0
    if os.environ.get('EP001_AUDITION_AUTHORIZED') != str(BUDGET):
        print(f'REFUSED: set EP001_AUDITION_AUTHORIZED={BUDGET} only after the reviewer has confirmed the credit balance and authorised up to {BUDGET} credits.'); return 3
    os.makedirs(OUT, exist_ok=True)
    for n, v in VOICES:
        p = subprocess.run(command(n, v, True), capture_output=True, text=True); print(p.stdout)
        if p.returncode != 0: print('stopped after a failed request; no automatic retry (a retry is another paid request)'); return 2
    return 0
if __name__ == '__main__': sys.exit(main())
