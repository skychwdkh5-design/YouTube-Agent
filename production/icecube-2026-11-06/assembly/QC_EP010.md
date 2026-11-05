# EP010 IceCube — QC of review cut v4 (2026-11-05)

Status: REVIEW CUT for the owner. Not uploaded, not scheduled, no queue entry.

## Episode number
EP010. EP009 = Tornado Scars (uploaded manually 2026-11-04, not in publish-data queue); no EP010 branch, queue item or file existed.

## Voice
ElevenLabs Adam (pNInz6obpgDQGcFmaJgB), eleven_multilingual_v2, one paid run approved by the owner on 2026-11-05 (4,865 chars, 3 chunks).
Text = VOICE_ONLY.txt (sha256 8f82e272...). Audio sha256 7220af5e..., 334.646 s, 789 aligned words, no warnings.
Backup: /mnt/project-files/icecube/voice/. Do not regenerate.

## Technical (measured on the final MP4)
- 1920x1080, 30/1 fps CFR, H.264 High, 10,122 frames; AAC 48 kHz stereo 192k; 337.4 s (5:37).
- Loudness -15.1 LUFS integrated, true peak -1.9 dBTP, LRA 2.6 LU.
- Ambience (original synthesized wind + low hum, no music) ~ -49 dB RMS in pauses vs voice ~ -19 dB: ~30 dB below.
- blackdetect (0.3 s) and freezedetect (n=0.002, 2.5 s): no events.
- SRT built from the provider word timings (89 cues), not burned in; upload as a caption track.

## Timeline shares (from shots.py, 74 shots)
live 103.5 s = 30.7% (target >= 30%), animation/visualization 216.5 s = 64.2% (>= 45%), photo 17.5 s = 5.2% (<= 25%).
Longest shot 8.3 s (A01 reveal, continuous camera move). No photo held over 4.4 s. No text-only cards.

## Hook
0-4.4 s real IceCube Lab photo ("this building"); 4.4 s cut under the snow; array with 1,450/2,450 m and 86 strings / 5,160 modules visible by ~9 s.

## Accuracy / labels
- V01 labelled as NASA 88-South Traverse 2019, "not IceCube construction" on first uses, short credit afterwards.
- NASA clips labelled "Visualization: NASA Goddard / Conceptual Image Lab"; Fermi overlay says gamma rays, not the neutrino.
- 5,160 always tied to the original array; 2026 upgrade shown as separate. Uncertainty region from A04 kept.
- Cherenkov overlay: "faster than light in ice, not faster than light in a vacuum".

## Rights
- P01 (CC BY-SA 4.0) shown whole and unmodified in the video (scaled on a plain background). The thumbnail crops/enhances it, so the thumbnail is offered under CC BY-SA 4.0 (stated in the description).
- P02 (CC BY 4.0) cropped/zoomed, noted. V01 source audio not used. No third-party music.

## Thumbnail
thumbnail_EP010.jpg 1280x720: thumbcheck objective PASS (saturation 0.65, luma std 69.4, white 5.1%, yellow 5.3%).
Subjective check vs the 4 reference covers: headline style and colours match; lower half is a schematic (marked) and is flatter than the references. Verdict: candidate, owner to confirm.

## Render cost (where time goes)
Intro test (7 shots, 31 s): 30 s wall. Full render: ~7 min wall on 4 cores; ~4 min of that is motion-compensated 23.976->30 fps on 4 camera-move V01 shots. Other 70 shots ~5 min. Re-renders reuse unchanged shots (cache), audio remix ~20 s.

## Not done / for the owner
- Watch the full cut in real time (subjective pacing, voice clarity, judder on V01 pans) — automated checks cannot replace it.
- Approve or revise thumbnail and title; burned-in captions were not added (SRT track instead).
- Publishing is a separate step with its own approval card.
