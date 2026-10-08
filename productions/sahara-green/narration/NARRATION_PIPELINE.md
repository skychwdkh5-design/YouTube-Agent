# EP001 narration pipeline (prepared; no paid request has been made)

Source of truth: `../script.md` (SCRIPT LOCK v1.1, body hash `d646001c83d3421d43510ece1926d7bd49bc197dcdde07b94fd2f4f3a049f335`). Nothing below edits it.

## 1. Narration-only text (done, free)
`python3 build_narration_text.py` writes `narration_text.txt` and `narration_manifest.json`.
- Starts at `## COLD OPEN`. The notes above it (about 1,160 characters: lock status, "Claim IDs ... not spoken", status marks) are **not** spoken. Running `voice.py --script script.md` directly would have voiced them: 11,676 characters instead of 10,518.
- Removes 9 headings and 54 bracket tags (`[P20 ✓]` etc.). The script contains 0 `[ON SCREEN]` lines (on-screen text lives in `storyboard.md`); the filter would remove them anyway.
- Verified: script body hash equals SCRIPT_LOCK.md; the text equals the yt-voice skill's own `spoken_text()` of the same body; 1,778 words, 37 paragraphs, 120 sentences (units S001-S120), 10,518 characters; narration text sha256 `101a143c9e96b3507153d95cdc8af76db56a945ae575050a3abbd374edddb091`.

## 2. Voice and settings (prepared, `voice_config.json`)
American English male narrator. Default channel narrator is Adam (`pNInz6obpgDQGcFmaJgB`, American, middle-aged); because ElevenLabs describes Adam as "brash, openly confident", run a 790-character listening test (S001-S004, S046-S049, S055-S058) with Adam, Brian, Bill (optionally Eric) before the full run. Model `eleven_multilingual_v2`, settings stability 0.55, similarity 0.75, style 0, speed 1.0, speaker boost on; tune from the sample toward 140-150 wpm. yt-voice now accepts `--voice-settings JSON` and `--context` (added in this step, backward compatible, 3 new tests); pronunciation fixes go through a dictionary, not the text (`pronunciation_guide.json`).

## 3. Commands (in order; step 3a and 3b are the only paid ones)
```
# free: plan and character count (voice.py bills 10,510 characters in 5 chunks; the file has 10,518 including paragraph breaks)
python3 ../../../.claude/skills/yt-voice/voice.py --script narration_text.txt --output voice/narration.wav --max-chars 10600 --voice-settings '{"stability":0.55,"similarity_boost":0.75,"style":0,"speed":1.0,"use_speaker_boost":true}' --context
# 3a PAID listening test (about 790 characters per voice): --text "<excerpts>" --voice-id <id> --output voice/sample_<name>.wav --confirm --max-chars 800
# 3b PAID full narration (10,518 characters): the same command as the free plan plus --confirm
python3 ../../../.claude/skills/yt-captions/captions.py --voice voice/narration.voice.json --out-dir captions/ --max-chars 64 --max-duration 5     # free: SRT, VTT, JSON
python3 cues.py verify voice/narration.voice.json   # provider words == narration text, word for word
python3 cues.py locate voice/narration.voice.json   # cues.json: start/end of S001-S120
python3 cues.py fit cues.json                        # schedules for the East Oweinat and Toshka sequences
```
`voice/` is outside Git (audio is large and licensed per run); the voice.json (text, timing, audio hash) is small and is committed with the review.

## 4. Timing, alignment, SRT
ElevenLabs returns character alignment; yt-voice keeps word timings only if the alignment matches the text exactly (otherwise no timing and no captions: nothing is estimated). yt-captions turns the words into phrase-sized SRT/VTT cues (max 64 characters, 2 lines, 5 s for mobile). The audio is the master clock for everything.

## 5. How narration controls the visuals
Sequences are defined in seconds; frame i is drawn at i / 30 s. After `cues.py locate`, `cues.py fit` returns each sequence's schedule from sentence anchors:
- East Oweinat: 1984 from the start of S047 ("This is East Oweinat") until 0.25 s before S049 ("Today, it's covered..."); then 2000, 2010, 2016, 2024 with 0.8 s dissolves, holds of 0.7-1.5 s and a zoom of 3.5-6 s; the zoom may run up to 1.5 s into S050 ("The water comes from below"). If the window is too short the solver reports the shortfall in seconds instead of squeezing (the delivered 21.7 s review cut will not fit: S047-S049 are 35 words, about 15 s at 145 wpm).
- Toshka: 1999 from S055; 2002 fully visible 0.3 s after S056 starts ("...full in 2002"), 2011 at S057 ("By 2012..."), 2021 at S058 ("In 2021..."); 2021 holds to the end of S058 plus 1 s.
The solver and the cue locator are covered by `test_cues.py` using simulated timings (labelled as such; never used for captions).

## 6. Open design points
1. The final render must put the two custom sequences into the film: yt-render has only still-image clips (`landsat`/`image`) with Ken Burns and crossfades, no video clip. Options: add a `video` clip type to yt-render (recommended: frame-accurate, no re-timing) or render segments and splice with ffmpeg.
2. Frame 2011 is January 2011 while the narration says "By 2012": acceptable as the nearest usable TM date, but it is a wording gap you may want to see (no usable TM or SLC-on scene exists after October 2011; Landsat 7 ETM+ 2012 has stripes).
3. The narrator voice choice (listening test), pronunciation fixes, final speed.
