# EP001 voice audition: exact commands (NOT executed; PAID)

Run only after the reviewer has (1) confirmed the available ElevenLabs credit balance and (2) authorised up to **2,031 credits**.
Model `eleven_multilingual_v2`; voice settings stability 0.55, similarity 0.75, style 0, speed 1.0, speaker boost on; identical text
(`sample_text.txt`, 677 characters, 1 request per voice, sha256 `a21adac1c73daae67bc4c3affd9602be7b421f731b628961cb941f2efe605642`).
No pronunciation dictionary. One request per voice, no automatic retry. Credits: 677 + 677 + 677 = 2,031.

From the repository root:

```bash
mkdir -p productions/sahara-green/narration/voice/audition
S='{"stability":0.55,"similarity_boost":0.75,"style":0,"speed":1.0,"use_speaker_boost":true}'
# 1  Brian  nPczCjzI2devNBz1zQrb   (677 credits)
python3 .claude/skills/yt-voice/voice.py --script productions/sahara-green/narration/audition/sample_text.txt --voice-id nPczCjzI2devNBz1zQrb --output productions/sahara-green/narration/voice/audition/sample_Brian.wav --model eleven_multilingual_v2 --voice-settings "$S" --max-chars 700 --auth proxy --confirm
# 2  Bill   pqHfZKP75CvOlQylNhV4   (677 credits)
python3 .claude/skills/yt-voice/voice.py --script productions/sahara-green/narration/audition/sample_text.txt --voice-id pqHfZKP75CvOlQylNhV4 --output productions/sahara-green/narration/voice/audition/sample_Bill.wav --model eleven_multilingual_v2 --voice-settings "$S" --max-chars 700 --auth proxy --confirm
# 3  Adam   pNInz6obpgDQGcFmaJgB   (677 credits)
python3 .claude/skills/yt-voice/voice.py --script productions/sahara-green/narration/audition/sample_text.txt --voice-id pNInz6obpgDQGcFmaJgB --output productions/sahara-green/narration/voice/audition/sample_Adam.wav --model eleven_multilingual_v2 --voice-settings "$S" --max-chars 700 --auth proxy --confirm
```

Safe wrapper (same three commands, guarded): `python3 productions/sahara-green/narration/audition/run_audition.py` prints and plan-checks them without sending anything; `--execute` is refused unless `EP001_AUDITION_AUTHORIZED=2031` is set.
Before running: `python3 productions/sahara-green/narration/audition/verify_sample.py` (free) must print `ALL_OK: true`.
After running: the WAV files stay out of Git; each `.voice.json` records the audio hash, the exact text and word timings.
The full narration (10,510 characters) is a separate step and is not generated until the reviewer has listened and selected the voice.
