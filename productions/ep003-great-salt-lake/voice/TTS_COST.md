# EP003 narration: exact cost basis (nothing has been paid or requested)

Locked text: `story/SCRIPT_LOCK.json` (hash of the spoken text); plan: `voice/tts_plan.json`.
- Characters sent to the provider: **4,795** (3 chunks, longest 1,698, cap 1,700; voice Adam `pNInz6obpgDQGcFmaJgB`). 39 of them are blank-line characters; joining paragraphs with single newlines would send **4,756** (changes pauses slightly; needs the owner's choice before the text is locked for TTS).
- Credits: 1 credit per character for `eleven_multilingual_v2` -> **4,795 credits** (the project's planning rule in `docs/production-knowledge/TTS_ELEVENLABS.md`, ASSUMED: the balance cannot be read with this key). A failed request is billed anyway (EP001: two 502s), so the plan stays at 1,700-character chunks with the persistent cache; rerunning a cached chunk costs nothing.
- USD: **not computable from here**: it depends on the owner's plan. Formula: 4.795 x (plan price per 1,000 credits). Example only (ASSUMED, check the plan page): at 22 USD per 100,000 credits -> about 1.05 USD.
- Needed from the owner before any paid run: (1) plan/balance, (2) approval in words: `orbital.py approve ep003-great-salt-lake tts --max-chars 4795 --quote "..."`, (3) a listen to the pronunciation of Gunnison, Gilbert, Farmington, Saltair, Newfoundland, GRACE, methyl mercury (the agent cannot listen).
