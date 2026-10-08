#!/usr/bin/env python3
"""EP001 full narration, PAID, cached per request. Narrator Adam, eleven_multilingual_v2.

Authorised by the reviewer: ONE complete generation in the five planned requests, at most 10,510 credits, no automatic retry,
each successful segment saved immediately, interrupted runs resume from the cache, a successful segment is never regenerated
without explicit approval (this script has no flag that does that).

  python3 generate_ep001.py --plan        # free: exact billable characters, chunks, cache state
  python3 generate_ep001.py --confirm     # PAID: sends only the segments that are not cached yet, one attempt each
  python3 generate_ep001.py --resplit 1700 [--confirm]   # request 1 stays cached; the rest in shorter requests (needs reviewer approval: the five-request plan hit a ~30 s gateway limit)
"""
import base64, hashlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REPO = os.path.dirname(os.path.dirname(ROOT))
sys.path.insert(0, os.path.join(REPO, '.claude', 'skills', 'yt-voice'))
import voice
BUDGET = 10510
VOICE_ID, VOICE_NAME, MODEL = 'pNInz6obpgDQGcFmaJgB', 'Adam', 'eleven_multilingual_v2'
SETTINGS = {'stability': 0.55, 'similarity_boost': 0.75, 'style': 0.0, 'speed': 1.0}          # exactly the four reviewer values
OUT = os.path.join(HERE, 'voice'); CACHE = os.path.join(OUT, 'cache'); LEDGER = os.path.join(OUT, 'ledger.json')
captured = {}
def key(text): return hashlib.sha256(json.dumps([text, VOICE_ID, MODEL, SETTINGS], sort_keys=True).encode()).hexdigest()[:24]
class Cached(voice.ElevenLabs):
    """ElevenLabs provider that writes every successful response to disk at once and answers from disk when it can."""
    chunks = []
    def synthesize(self, text, voice_id, context=None):
        k = key(text); mp3, js = os.path.join(CACHE, f'{k}.mp3'), os.path.join(CACHE, f'{k}.json')
        if os.path.exists(mp3) and os.path.exists(js):
            d = json.load(open(js)); print(f'  cached  {k}  ({len(text)} chars, no request)', flush=True)
            return {'audio': open(mp3, 'rb').read(), 'format': 'mp3', 'alignment': d['alignment']}
        spent = usage_today(); remaining = sum(len(c) for c in Cached.chunks if not os.path.exists(os.path.join(CACHE, key(c) + '.mp3')))
        if spent + remaining * RATE_MARGIN > BUDGET: raise BillingStop(f'budget guard: {spent:.0f} credits used today + {remaining} uncached characters x {RATE_MARGIN} would exceed {BUDGET}; stopped for approval')
        before = spent
        print(f'  REQUEST {k}  ({len(text)} chars): sending ONE paid request, no retry', flush=True)
        t0 = time.time()
        try:
            res = super().synthesize(text, voice_id, context=context)      # raises VoiceError on any failure; nothing is retried
        except voice.VoiceError as e:
            add({'key': k, 'characters': len(text), 'credits': None, 'status': 'failed', 'error': str(e)[:200], 'seconds': round(time.time() - t0, 1), 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}); raise
        h = captured.get('headers', {})
        cost = int(h['character-cost']) if str(h.get('character-cost', '')).isdigit() else None
        after = usage_today()
        for _ in range(12):            # the usage endpoint lags the request by a few seconds to a minute: wait for it to catch up before judging
            if cost is None or abs((after - before) - cost) <= 1: break
            time.sleep(10); after = usage_today()
        os.makedirs(CACHE, exist_ok=True)
        tmp = mp3 + '.tmp'; open(tmp, 'wb').write(res['audio']); os.replace(tmp, mp3)
        json.dump({'alignment': res['alignment'], 'characters': len(text), 'headers': h}, open(js + '.tmp', 'w')); os.replace(js + '.tmp', js)
        add({'key': k, 'characters': len(text), 'credits': cost, 'usage_before': before, 'usage_after': after, 'request_id': h.get('request-id'), 'seconds': round(time.time() - t0, 1), 'status': 'ok', 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
        print(f'  saved   {k}  character-cost header: {h.get("character-cost")}; usage today {before:.0f} -> {after:.0f}', flush=True)
        if cost is None or abs((after - before) - cost) > 1 or not (0.2 <= cost / len(text) <= 0.8):
            raise BillingStop(f'unexpected billing: header {cost}, usage delta {after - before:.0f}, {len(text)} characters; the segment is saved; stopped')
        return res
def usage_today():
    """Credits ElevenLabs reports as used today (UTC), from the free /v1/usage/character-stats endpoint. Conservative: everything counted today is treated as ours."""
    import urllib.request, datetime
    now = int(time.time() * 1000); d0 = int(datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    url = f'https://api.elevenlabs.io/v1/usage/character-stats?start_unix={d0}&end_unix={now}&aggregation_interval=day'
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'yt-voice'}), timeout=30) as r:
        return float(sum(json.load(r)['usage'].get('All', [])))
RATE_MARGIN = 0.55          # forward projection: measured rate is 0.44 credits per character; 25 percent margin
class BillingStop(voice.VoiceError):
    pass
def ledger():
    return json.load(open(LEDGER)) if os.path.exists(LEDGER) else {'voice': VOICE_NAME, 'voice_id': VOICE_ID, 'model': MODEL, 'settings': SETTINGS, 'budget_credits': BUDGET, 'requests': []}
def add(entry):
    os.makedirs(OUT, exist_ok=True); d = ledger(); d['requests'].append(entry); json.dump(d, open(LEDGER + '.tmp', 'w'), indent=1); os.replace(LEDGER + '.tmp', LEDGER)
def record_headers():
    real = voice.urllib.request.urlopen
    class R:
        def __init__(s, r): s.r = r
        def __enter__(s): s.r.__enter__(); return s
        def __exit__(s, *a): return s.r.__exit__(*a)
        def read(s, *a): captured['headers'] = {k.lower(): v for k, v in s.r.headers.items() if k.lower() in ('character-cost', 'request-id', 'content-type')}; return s.r.read(*a)
    voice.urllib.request.urlopen = lambda req, timeout=None: R(real(req, timeout=timeout))
def main():
    confirm = '--confirm' in sys.argv
    raw = open(os.path.join(HERE, 'narration_text.txt'), encoding='utf-8').read()
    man = json.load(open(os.path.join(HERE, 'narration_manifest.json')))
    assert hashlib.sha256(raw.encode()).hexdigest() == man['narration_text_sha256'], 'narration text differs from the locked one'
    text, removed = voice.spoken_text(raw); assert removed == []
    chunks = voice.split_chunks(text, 2500)
    resplit = int(sys.argv[sys.argv.index('--resplit') + 1]) if '--resplit' in sys.argv else None
    if resplit:          # request 1 stays exactly as cached (2,276 characters); the rest is re-split into shorter requests (same text, same characters)
        chunks = [chunks[0]] + voice.split_chunks('\n\n'.join(chunks[1:]), resplit)
    billed = sum(len(c) for c in chunks)
    print(f'narrator {VOICE_NAME} {VOICE_ID}, model {MODEL}, settings {SETTINGS}')
    print(f'billable characters: {billed} in {len(chunks)} requests ({[len(c) for c in chunks]}); budget {BUDGET}; cached: {[os.path.exists(os.path.join(CACHE, key(c) + ".mp3")) for c in chunks]}')
    assert resplit or len(chunks) == 5, 'expected the five planned requests'
    if billed > BUDGET: print('STOP: expected charge exceeds the authorised budget'); return 3
    if not confirm: print('plan only; nothing sent'); return 0
    os.makedirs(OUT, exist_ok=True); os.makedirs(CACHE, exist_ok=True); record_headers()
    options = {'max_chars': BUDGET, 'max_chunk_chars': 2500, 'timeout_s': 180, 'auth': 'proxy', 'language': 'en', 'voice_settings': SETTINGS, 'context': True, 'model': MODEL}
    p = voice.plan(text, 'elevenlabs', VOICE_ID, os.path.join(OUT, 'narration.wav'), options)
    Cached.chunks = chunks
    base = usage_today(); print(f'confirmed charges today before this run: {base:.0f} credits (ceiling {BUDGET})'); 
    if base + sum(len(c) for c in chunks if not os.path.exists(os.path.join(CACHE, key(c) + '.mp3'))) * RATE_MARGIN > BUDGET: print('STOP: projected total exceeds the ceiling'); return 3
    p['provider'] = Cached(options); p['voice_name'] = VOICE_NAME
    if resplit: p['chunks'] = chunks; p['characters'] = billed
    try:
        res = voice.generate(p, options, overwrite=True)
    except voice.VoiceError as e:
        try: print(f'usage today at the stop: {usage_today():.0f} credits')
        except Exception: pass
        print('STOPPED:', e, '(successful segments are cached; rerun resumes; nothing is retried automatically)'); return 2
    print(json.dumps({k: res[k] for k in ('status', 'output', 'duration', 'characters', 'chunks', 'timing', 'words')}, indent=1))
    d = ledger(); d['total_credits_header'] = sum(e['credits'] for e in d['requests'] if e.get('credits') is not None); d['requests_ok'] = sum(1 for e in d['requests'] if e['status'] == 'ok'); json.dump(d, open(LEDGER, 'w'), indent=1)
    print('credits (character-cost headers):', d['total_credits_header'], 'requests:', d['requests_ok']); return 0
if __name__ == '__main__': sys.exit(main())
