# EP010 IceCube — QC of final master (2026-11-05)

Status: FINAL MASTER (cover B opening) for owner review (sha256 3571e59a...). Not uploaded, not scheduled, no queue entry.

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
live 102.7 s = 30.5% (target >= 30%), animation/visualization 219.1 s = 64.9% (>= 45%), photo 15.6 s = 4.6% (<= 25%).
Longest shot 8.4 s (A01 descent). No photo held over 4.1 s. No text-only cards.

## Hook
0.0 s approved cover B, full frame; from 0.3 s camera moves to the lab (headline exits left), then down the yellow arrow; 2.6 s cut on the downward move into A01 with sensors and the 1,450 m mark, 2,450 m by ~3.3 s.

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

## Final master changes (owner notes 2026-11-05)
- Intro: descent starts at 2.5 s, sensors at ~3.5 s; voice timing untouched.
- Label-clipping zooms removed at 2:33-2:37 (A02) and 2:57-3:01 (replaced by live cabin shot with the speed-of-light overlay); also softened at 0:10, 1:23, 1:29, 4:43, 5:14.
- Middle (2:37-3:36): particle passes (A03) -> interaction and light (A03) -> sensors fire in order (A04, A01 colour wave) -> direction appears (A04); repeated A03 crops removed.
- 5:10-5:15: "ICECUBE UPGRADE / DEPLOYED 2026" now on the IceCube installation schematic, not on 2019 traverse footage.
- ~1:04-1:20 judder: NASA particle animation (60 fps webm with jittery timestamps) was resampled with an uneven 2-3-frame cadence and ran 0.1 s past its last frame. Now every second source frame is taken and the in-point moved; frame-difference check shows an even cadence and no held frames.
- Thumbnail: TELESCOPE / UNDER THE ICE kept; "DOWN TO 2.5 KM" at the lowest sensor row.
- Final export recalculated changed scenes only (25 + 1 of 74 shots), rest from cache.
- Sync: 52 speech onsets after pauses in the MP4 vs provider word starts: median -42 ms, range -100..+9 ms (detector lag). SRT: 89 cues, monotonic, last cue ends 5:34.646 inside the 5:37.4 file.

## Cover B opening (owner approval 2026-11-05 08:58Z)
- Cover B ("2.5 KM DOWN", owner-supplied illustration, sha256 9fabeab2...) is the YouTube thumbnail (1280x720, thumbcheck objective PASS: luma std 77.1, white 11.3%, yellow 8.2%) and frame 0 of the video (mean abs difference to the cover after scaling: ~3/255).
- 0.3-2.6 s one continuous curved camera move (Bezier path, eased), zoom up to 2x on the 1672x941 source, so those frames are softer than native 1080p.
- 2.6 s: A01 starts 1.4x high in the frame and keeps moving down (ease-out) to the full schematic; title and side note leave the frame during the move.
- 10.86-16.63 s: NASA particle-journey visualization. To avoid showing it twice, the 1:04 shot is now live field footage with the overlay NEUTRINOS / NO ELECTRIC CHARGE / ALMOST NO MASS.
- Shares: live 107.5 s = 31.9%, animation 214.2 s = 63.5%, stills 15.7 s = 4.7%.
- Re-rendered shots: 0, 1, 2, 14 (rest from cache). Audio stream byte-identical to the previous master, so voice and SRT sync are unchanged (re-measured: speech onsets -100..+9 ms vs word timings).
