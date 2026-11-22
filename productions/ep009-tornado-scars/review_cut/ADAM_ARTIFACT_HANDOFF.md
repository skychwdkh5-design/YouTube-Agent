# EP009 FINAL Adam audio handoff — verified 2026-11-04

## Authoritative paid artifact — NEVER generate again without separate owner approval

- Successful GitHub Actions workflow run: https://github.com/skychwdkh5-design/YouTube-Agent/actions/runs/41686927185
- Artifact name: `EP009-Adam-audio-and-timings-41686927185` (GitHub Actions artifact ID 13254119704)
- Download via an authenticated gh CLI installation with repo access:
  `gh run download 41686927185 -R skychwdkh5-design/YouTube-Agent -n EP009-Adam-audio-and-timings-41686927185 -D /path/to/ep009/adam`
- Alternative: owner has ZIP downloaded to iPad, or download via the run web page → Artifacts.
- Artifact expiry: 2026-11-10 17:44:21 UTC. Do not rely on later download availability.
- Owner uploaded a copy to ChatGPT; ZIP checked independently, and SHA-256 of each WAV verified against provider metadata.
- Do not commit audio WAV into Git history. Store in renderer's working directory and backup appropriate deliverable storage with owner authorization.

## Exact contents and verified SHA-256

| File | Duration | Provider characters | Aligned words | SHA-256 |
|---|---:|---:|---:|---|
| `long.wav` + `long.voice.json` | 330.466s | 4744 | 751 | `d8c87338277524470eba8ccd43ffbe9a46b7349e66e62fd83c9985257880d277` |
| `short_01.wav` + `short_01.voice.json` | 20.852s | 343 | 55 | `8c789b72517352cf3c9e015a992d9e7f7d0a65963e1362f341a0062308d2756b` |
| `short_02.wav` + `short_02.voice.json` | 27.864s | 398 | 60 | `bd666f44ae7e1f67ffc9cfd6209490baba462d389d8035d1da4de5f1c474e5ea` |

The ZIP contains `EP009_ADAM_MANIFEST.json` and each pair above. Model `eleven_multilingual_v2`, voice ID `pNInz6obpgDQGcFmaJgB` (Adam). Timing metadata `timing.source=provider`, `timing.level=word`, warnings empty.

## Critical editorial and technical requirements

1. Existing Long review V3 duration 378.6s, new narration 330.466s, difference **48.134s**. Do NOT replace WAV under fixed Flite timestamps or simply truncate. Retime each scene and subtitles using `*.voice.json` exact word timing; preserve context shot coverage and all key visual claims. Duration will change.
2. Shorts new voice durations 20.852s and 27.864s. Rebuild their caption/sound synchronization too.
3. Thumbnail #4 `SCAR FROM SPACE` approved, intro Thumbnail–Hook Match already implemented. Keep it and preserve caption overlays.
4. **GOES RIGHTS STILL BLOCKING**: `noaa_goes13_outbreak_2011.mp4` has unresolved third-party provenance. Do not include in release. The NASA replacement MOV attempted in Actions workflow `ep009-acquire-nasa-goes.yml` failed with network unreachable; it is NOT present. Either obtain approved NASA footage or edit the visuals and narration for allowed substitutes. The Adam audio has ALREADY been paid and recorded: any script changes now require precise local trims/cuts or owner-approved new TTS for affected phrases; do not regenerate all 3.
5. Other NASA/USGS originals M04/M05/M06 ARE committed in `media_original/`.
6. Preserve final voice audio, show owner the updated Long and 2 Shorts with QC and source rights, no YouTube uploads, no schedule, no paid regenerations or experimental motion work unless owner specifically approves.
7. For `gh` access failure, ask for the ZIP as a conversation attachment, not another ElevenLabs run. Existing GitHub Actions artifact belongs to the repo workflow run, independent of its branches.

## QC gates

- Check WAV metadata sha256, exact audio spans, word alignment.
- Scene-to-word matching for every factual claim, especially original 2011 weather imagery.
- H.264/AAC, target 1920×1080/30 for Long and 1080×1920 for Shorts, no frozen/black frames, subtitle readability, loudness/peak QC, rights, first-3-sec hook match.
- Deliver finished MP4, English SRT and QC report for owner review before scheduling.
